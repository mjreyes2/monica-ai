#!/usr/bin/env/python3
"""Recipe for training a wav2vec-based CTC ASR system for Monica's voice.
Based on SpeechBrain LibriSpeech recipe, adapted for custom dataset.

To run this recipe:
> python train_monica.py hparams_monica.yaml

Authors
 * Adapted from SpeechBrain LibriSpeech recipe
 * Original authors: Rudolf A Braun, Titouan Parcollet, Sung-Lin Yeh, et al.
"""

import os
import sys
from pathlib import Path
import gc

import torch
from hyperpyyaml import load_hyperpyyaml

import speechbrain as sb
from speechbrain.utils.distributed import if_main_process, run_on_main
from speechbrain.utils.logger import get_logger

logger = get_logger(__name__)

# Set environment variables for better CUDA memory management
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128,expandable_segments:True'
os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # Allow async ops for better performance

# Enable TF32 for better performance on Ampere GPUs (if available)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


# Define training procedure
class ASR(sb.Brain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grad_accumulation_step = 0
        # Initialize gradient scaler for fp16 mixed precision
        if hasattr(self.hparams, 'precision') and self.hparams.precision == "fp16":
            self.scaler = torch.cuda.amp.GradScaler()

        # Early stopping tracking
        self.best_metric_value = float('inf')  # Lower is better for WER/CER
        self.epochs_without_improvement = 0
        self.early_stopping_triggered = False

    def compute_forward(self, batch, stage):
        """Forward computations from the waveform batches to the output probabilities."""
        batch = batch.to(self.device)
        wavs, wav_lens = batch.sig
        wavs, wav_lens = wavs.to(self.device), wav_lens.to(self.device)

        # Downsample the inputs if specified
        if hasattr(self.modules, "downsampler"):
            wavs = self.modules.downsampler(wavs)

        # Add waveform augmentation if specified.
        if stage == sb.Stage.TRAIN and hasattr(self.hparams, "wav_augment"):
            wavs, wav_lens = self.hparams.wav_augment(wavs, wav_lens)

        # Forward pass

        # Handling SpeechBrain vs HuggingFace pretrained models
        if hasattr(self.modules, "extractor"):  # SpeechBrain pretrained model
            latents = self.modules.extractor(wavs)
            feats = self.modules.encoder_wrapper(latents, wav_lens=wav_lens)[
                "embeddings"
            ]
        else:  # HuggingFace pretrained model
            # Enable gradient checkpointing for wav2vec2 to save memory
            if stage == sb.Stage.TRAIN:
                if hasattr(self.modules.wav2vec2.model, 'gradient_checkpointing_enable'):
                    self.modules.wav2vec2.model.gradient_checkpointing_enable()
                # Use autocast for mixed precision
                if self.hparams.precision == "fp16":
                    with torch.cuda.amp.autocast():
                        feats = self.modules.wav2vec2(wavs, wav_lens)
                else:
                    feats = self.modules.wav2vec2(wavs, wav_lens)
            else:
                feats = self.modules.wav2vec2(wavs, wav_lens)

        x = self.modules.enc(feats)

        # Compute outputs
        p_tokens = None
        logits = self.modules.ctc_lin(x)

        # Upsample the inputs if they have been highly downsampled
        if hasattr(self.hparams, "upsampling") and self.hparams.upsampling:
            logits = logits.view(
                logits.shape[0], -1, self.hparams.output_neurons
            )

        p_ctc = self.hparams.log_softmax(logits)

        if stage == sb.Stage.VALID:
            # Beam search (helps avoid blank-only outputs). Fallback to greedy if beam fails.
            try:
                p_tokens = self.valid_searcher(p_ctc, wav_lens)
            except Exception as e:
                logger.warning(f"[VALID] Beam search failed ({e}); falling back to greedy decode.")
                p_tokens = sb.decoders.ctc_greedy_decode(
                    p_ctc, wav_lens, blank_id=self.hparams.blank_index
                )
        elif stage == sb.Stage.TEST:
            try:
                p_tokens = test_searcher(p_ctc, wav_lens)
            except Exception as e:
                logger.warning(f"[TEST] Beam search failed ({e}); falling back to greedy decode.")
                p_tokens = sb.decoders.ctc_greedy_decode(
                    p_ctc, wav_lens, blank_id=self.hparams.blank_index
                )

            candidates = []
            scores = []

            for batch in p_tokens:
                candidates.append([hyp.text for hyp in batch])
                scores.append([hyp.score for hyp in batch])

            if hasattr(self.hparams, "rescorer"):
                p_tokens, _ = self.hparams.rescorer.rescore(candidates, scores)

        return p_ctc, wav_lens, p_tokens

    def compute_objectives(self, predictions, batch, stage):
        """Computes the loss (CTC+NLL) given predictions and targets."""

        p_ctc, wav_lens, predicted_tokens = predictions

        ids = batch.id
        tokens, tokens_lens = batch.tokens

        # Labels must be extended if parallel augmentation or concatenated
        # augmentation was performed on the input (increasing the time dimension)
        if stage == sb.Stage.TRAIN and hasattr(self.hparams, "wav_augment"):
            (
                tokens,
                tokens_lens,
            ) = self.hparams.wav_augment.replicate_multiple_labels(
                tokens, tokens_lens
            )

        loss_ctc = self.hparams.ctc_cost(p_ctc, tokens, wav_lens, tokens_lens)
        loss = loss_ctc

        # Gradient accumulation: scale loss by accumulation factor
        if stage == sb.Stage.TRAIN and hasattr(self.hparams, 'grad_accumulation_factor'):
            loss = loss / self.hparams.grad_accumulation_factor

        # Aggressive memory clearing to prevent OOM
        if stage == sb.Stage.TRAIN:
            # Clear cache every step to prevent fragmentation
            torch.cuda.empty_cache()
            # Delete intermediate tensors if they exist
            if 'p_ctc' in locals():
                del p_ctc
            gc.collect()

        if stage == sb.Stage.VALID:
            # Beam search hypotheses; take best hyp.text
            predicted_words = []
            for hyps in predicted_tokens:
                text = ""
                if isinstance(hyps, list) and len(hyps) > 0 and hasattr(hyps[0], "text"):
                    text = hyps[0].text
                elif isinstance(hyps, str):
                    text = hyps
                else:
                    # fallback: treat as raw indices tensor
                    collapsed = self.tokenizer.collapse_indices_ndim(hyps)
                    chars = self.tokenizer.decode_ndim(collapsed)
                    text = "".join(chars)
                words = text.split() if text.strip() else [""]
                predicted_words.append(words)
                if len(predicted_words) <= 3:
                    logger.info(f"[DECODE] beam_text='{text[:50]}' words={words[:5]}")
        elif stage == sb.Stage.TEST:
            if hasattr(self.hparams, "rescorer"):
                predicted_words = [
                    hyp[0].split(" ") for hyp in predicted_tokens
                ]
            else:
                predicted_words = [
                    hyp[0].text.split(" ") for hyp in predicted_tokens
                ]

        if stage != sb.Stage.TRAIN:
            target_words = [wrd.split(" ") for wrd in batch.wrd]
            self.wer_metric.append(ids, predicted_words, target_words)
            self.cer_metric.append(ids, predicted_words, target_words)

        return loss

    def on_stage_start(self, stage, epoch):
        """Gets called at the beginning of each epoch"""
        if stage != sb.Stage.TRAIN:
            self.cer_metric = self.hparams.cer_computer()
            self.wer_metric = self.hparams.error_rate_computer()

        # Freeze wav2vec encoder for warmup epochs to avoid blank collapse
        warmup = getattr(self.hparams, "freeze_warmup_epochs", 0)
        if stage == sb.Stage.TRAIN and warmup > 0:
            if epoch <= warmup:
                if hasattr(self.modules, "wav2vec2"):
                    self.modules.wav2vec2.freeze = True
                    # Also set requires_grad False explicitly to avoid optimizer steps
                    for p in self.modules.wav2vec2.parameters():
                        p.requires_grad = False
                    logger.info(f"[WARMUP] Freezing wav2vec encoder (epoch {epoch}/{warmup})")
            else:
                if hasattr(self.modules, "wav2vec2"):
                    self.modules.wav2vec2.freeze = False
                    for p in self.modules.wav2vec2.parameters():
                        p.requires_grad = True
                    logger.info("[WARMUP] Unfreezing wav2vec encoder")

        if stage == sb.Stage.TEST:
            if hasattr(self.hparams, "rescorer"):
                self.hparams.rescorer.move_rescorers_to_device()

    def on_stage_end(self, stage, stage_loss, epoch):
        """Gets called at the end of an epoch."""
        # Aggressive GPU memory cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()

        # Reset gradient accumulation counter
        if stage == sb.Stage.TRAIN:
            self.grad_accumulation_step = 0

        # Compute/store important stats
        stage_stats = {"loss": stage_loss}
        if stage == sb.Stage.TRAIN:
            self.train_stats = stage_stats
        else:
            stage_stats["CER"] = self.cer_metric.summarize("error_rate")
            stage_stats["WER"] = self.wer_metric.summarize("error_rate")

        # Perform end-of-iteration things, like annealing, logging, etc.
        if stage == sb.Stage.VALID:
            old_lr_model, new_lr_model = self.hparams.lr_annealing_model(
                stage_stats["loss"]
            )
            old_lr_wav2vec, new_lr_wav2vec = self.hparams.lr_annealing_wav2vec(
                stage_stats["loss"]
            )
            sb.nnet.schedulers.update_learning_rate(
                self.model_optimizer, new_lr_model
            )
            sb.nnet.schedulers.update_learning_rate(
                self.wav2vec_optimizer, new_lr_wav2vec
            )
            self.hparams.train_logger.log_stats(
                stats_meta={
                    "epoch": epoch,
                    "lr_model": old_lr_model,
                    "lr_wav2vec": old_lr_wav2vec,
                },
                train_stats=self.train_stats,
                valid_stats=stage_stats,
            )
            self.checkpointer.save_and_keep_only(
                meta={"WER": stage_stats["WER"]},
                min_keys=["WER"],
            )

            # Early stopping check
            if hasattr(self.hparams, 'early_stopping_enabled') and self.hparams.early_stopping_enabled:
                metric_name = getattr(self.hparams, 'early_stopping_metric', 'WER')
                patience = getattr(self.hparams, 'early_stopping_patience', 5)
                min_delta = getattr(self.hparams, 'early_stopping_min_delta', 0.001)

                current_metric = stage_stats.get(metric_name, float('inf'))

                # Check if we have improvement (lower is better for WER/CER)
                if current_metric < (self.best_metric_value - min_delta):
                    # Improvement detected
                    self.best_metric_value = current_metric
                    self.epochs_without_improvement = 0
                    logger.info(f"[EARLY STOP] [OK] New best {metric_name}: {current_metric:.4f}")
                else:
                    # No improvement
                    self.epochs_without_improvement += 1
                    logger.info(f"[EARLY STOP] No improvement for {self.epochs_without_improvement}/{patience} epochs (best {metric_name}: {self.best_metric_value:.4f})")

                    if self.epochs_without_improvement >= patience:
                        self.early_stopping_triggered = True
                        logger.info(f"[EARLY STOP] [WARN] Stopping training - no improvement for {patience} epochs")
                        logger.info(f"[EARLY STOP] Best {metric_name}: {self.best_metric_value:.4f} (checkpoint already saved)")
                        # Raise exception to stop training
                        raise StopIteration(f"Early stopping: no improvement in {metric_name} for {patience} epochs")
        elif stage == sb.Stage.TEST:
            self.hparams.train_logger.log_stats(
                stats_meta={"Epoch loaded": self.hparams.epoch_counter.current},
                test_stats=stage_stats,
            )
            if if_main_process():
                with open(
                    self.hparams.test_wer_file, "w", encoding="utf-8"
                ) as w:
                    self.wer_metric.write_stats(w)

    def fit_batch(self, batch):
        """Custom fit_batch with gradient accumulation support."""
        # Check if we should accumulate gradients
        should_step = True
        grad_accumulation_factor = getattr(self.hparams, 'grad_accumulation_factor', 1)

        if grad_accumulation_factor > 1:
            self.grad_accumulation_step += 1
            should_step = (self.grad_accumulation_step % grad_accumulation_factor == 0)

        # Forward pass with mixed precision if enabled
        if self.hparams.precision == "fp16" and hasattr(self, 'scaler'):
            with torch.cuda.amp.autocast():
                outputs = self.compute_forward(batch, sb.Stage.TRAIN)
                loss = self.compute_objectives(outputs, batch, sb.Stage.TRAIN)

            # Scale loss and backward with gradient scaler
            self.scaler.scale(loss).backward()

            # Only step optimizer if we've accumulated enough gradients
            if should_step:
                # Detect if wav2vec params require grad (e.g., frozen during warmup)
                train_wav2vec = False
                if hasattr(self.modules, "wav2vec2"):
                    train_wav2vec = any(
                        p.requires_grad for p in self.modules.wav2vec2.parameters()
                    )

                # Unscale gradients and clip
                self.scaler.unscale_(self.model_optimizer)
                if train_wav2vec:
                    self.scaler.unscale_(self.wav2vec_optimizer)

                # Optional gradient clipping
                if hasattr(self.hparams, 'grad_clip'):
                    torch.nn.utils.clip_grad_norm_(
                        self.modules.parameters(),
                        self.hparams.grad_clip
                    )

                # Optimizer step with scaler
                self.scaler.step(self.model_optimizer)
                if train_wav2vec:
                    self.scaler.step(self.wav2vec_optimizer)
                self.scaler.update()

                # Zero gradients after step
                self.model_optimizer.zero_grad()
                self.wav2vec_optimizer.zero_grad()
        else:
            # Standard fp32 training
            outputs = self.compute_forward(batch, sb.Stage.TRAIN)
            loss = self.compute_objectives(outputs, batch, sb.Stage.TRAIN)
            loss.backward()

            if should_step:
                train_wav2vec = False
                if hasattr(self.modules, "wav2vec2"):
                    train_wav2vec = any(
                        p.requires_grad for p in self.modules.wav2vec2.parameters()
                    )
                if hasattr(self.hparams, 'grad_clip'):
                    torch.nn.utils.clip_grad_norm_(
                        self.modules.parameters(),
                        self.hparams.grad_clip
                    )
                self.model_optimizer.step()
                if train_wav2vec:
                    self.wav2vec_optimizer.step()
                self.model_optimizer.zero_grad()
                self.wav2vec_optimizer.zero_grad()

        return loss.detach().cpu()

    def init_optimizers(self):
        "Initializes the wav2vec2 optimizer and model optimizer"
        # Handling SpeechBrain vs HuggingFace pretrained models
        if hasattr(self.modules, "extractor"):  # SpeechBrain pretrained model
            self.wav2vec_optimizer = self.hparams.wav2vec_opt_class(
                self.modules.encoder_wrapper.parameters()
            )

        else:  # HuggingFace pretrained model
            self.wav2vec_optimizer = self.hparams.wav2vec_opt_class(
                self.modules.wav2vec2.parameters()
            )

        self.model_optimizer = self.hparams.model_opt_class(
            self.hparams.model.parameters()
        )

        # save the optimizers in a dictionary
        # the key will be used in `freeze_optimizers()`
        self.optimizers_dict = {
            "model_optimizer": self.model_optimizer,
        }
        if not self.hparams.freeze_wav2vec:
            self.optimizers_dict["wav2vec_optimizer"] = self.wav2vec_optimizer

        if self.checkpointer is not None:
            self.checkpointer.add_recoverable(
                "wav2vec_opt", self.wav2vec_optimizer
            )
            self.checkpointer.add_recoverable("modelopt", self.model_optimizer)


def dataio_prepare(hparams):
    """This function prepares the datasets to be used in the brain class.
    It also defines the data processing pipeline through user-defined functions.
    """
    data_folder = hparams["data_folder"]

    train_data = sb.dataio.dataset.DynamicItemDataset.from_csv(
        csv_path=hparams["train_csv"],
        replacements={"data_root": data_folder},
    )

    if hparams["sorting"] == "ascending":
        # we sort training data to speed up training and get better results.
        train_data = train_data.filtered_sorted(sort_key="duration")
        # when sorting do not shuffle in dataloader ! otherwise is pointless
        hparams["train_dataloader_opts"]["shuffle"] = False

    elif hparams["sorting"] == "descending":
        train_data = train_data.filtered_sorted(
            sort_key="duration", reverse=True
        )
        # when sorting do not shuffle in dataloader ! otherwise is pointless
        hparams["train_dataloader_opts"]["shuffle"] = False

    elif hparams["sorting"] == "random":
        pass

    else:
        raise NotImplementedError(
            "sorting must be random, ascending or descending"
        )

    valid_data = sb.dataio.dataset.DynamicItemDataset.from_csv(
        csv_path=hparams["valid_csv"],
        replacements={"data_root": data_folder},
    )
    valid_data = valid_data.filtered_sorted(sort_key="duration")

    # test is separate
    test_datasets = {}
    for csv_file in hparams["test_csv"]:
        name = Path(csv_file).stem
        test_datasets[name] = sb.dataio.dataset.DynamicItemDataset.from_csv(
            csv_path=csv_file, replacements={"data_root": data_folder}
        )
        test_datasets[name] = test_datasets[name].filtered_sorted(
            sort_key="duration"
        )

    datasets = [train_data, valid_data] + [i for k, i in test_datasets.items()]

    # 2. Define audio pipeline:
    @sb.utils.data_pipeline.takes("wav")
    @sb.utils.data_pipeline.provides("sig")
    def audio_pipeline(wav):
        sig = sb.dataio.dataio.read_audio(wav)
        return sig

    sb.dataio.dataset.add_dynamic_item(datasets, audio_pipeline)
    label_encoder = sb.dataio.encoder.CTCTextEncoder()

    # 3. Define text pipeline:
    @sb.utils.data_pipeline.takes("wrd")
    @sb.utils.data_pipeline.provides(
        "wrd", "char_list", "tokens_list", "tokens"
    )
    def text_pipeline(wrd):
        yield wrd
        char_list = list(wrd)
        yield char_list
        tokens_list = label_encoder.encode_sequence(char_list)
        yield tokens_list
        tokens = torch.LongTensor(tokens_list)
        yield tokens

    sb.dataio.dataset.add_dynamic_item(datasets, text_pipeline)

    lab_enc_file = os.path.join(hparams["save_folder"], "label_encoder.txt")
    special_labels = {
        "blank_label": hparams["blank_index"],
    }
    label_encoder.load_or_create(
        path=lab_enc_file,
        from_didatasets=[train_data],
        output_key="char_list",
        special_labels=special_labels,
        sequence_input=True,
    )

    # 4. Set output:
    sb.dataio.dataset.set_output_keys(
        datasets,
        ["id", "sig", "wrd", "char_list", "tokens"],
    )

    return train_data, valid_data, test_datasets, label_encoder


if __name__ == "__main__":
    # CLI:
    hparams_file, run_opts, overrides = sb.parse_arguments(sys.argv[1:])

    # create ddp_group with the right communication protocol
    sb.utils.distributed.ddp_init_group(run_opts)

    with open(hparams_file, encoding="utf-8") as fin:
        hparams = load_hyperpyyaml(fin, overrides)

    # Create experiment directory
    sb.create_experiment_directory(
        experiment_directory=hparams["output_folder"],
        hyperparams_to_save=hparams_file,
        overrides=overrides,
    )

    # Skip LibriSpeech data prep since we already have CSVs
    # Data prep is already done - we have train.csv and val.csv ready

    # here we create the datasets objects as well as tokenization and encoding
    train_data, valid_data, test_datasets, label_encoder = dataio_prepare(
        hparams
    )

    # CRITICAL FIX: Get actual vocabulary size from CTCTextEncoder
    # The encoder creates vocabulary dynamically from training data
    actual_vocab_size = len(label_encoder)
    print(f"[VOCAB] CTCTextEncoder vocabulary size: {actual_vocab_size}")
    print(f"[VOCAB] Vocabulary: {label_encoder.ind2lab}")
    
    # Check if hparams output_neurons matches actual vocab size
    if hparams["output_neurons"] != actual_vocab_size:
        print(f"[VOCAB] WARNING: hparams output_neurons ({hparams['output_neurons']}) != actual vocab size ({actual_vocab_size})")
        print(f"[VOCAB] Rebuilding ctc_lin layer with correct output size...")
        
        # Rebuild the ctc_lin layer with correct output neurons
        import torch.nn as nn
        hparams["output_neurons"] = actual_vocab_size
        
        # Create new linear layer with correct output size
        new_ctc_lin = sb.nnet.linear.Linear(
            input_size=hparams["dnn_neurons"],
            n_neurons=actual_vocab_size
        )
        
        # Replace in modules
        hparams["modules"]["ctc_lin"] = new_ctc_lin
        hparams["ctc_lin"] = new_ctc_lin
        
        # Update model ModuleList
        hparams["model"] = nn.ModuleList([hparams["enc"], new_ctc_lin])
        
        print(f"[VOCAB] ctc_lin layer rebuilt: {hparams['dnn_neurons']} -> {actual_vocab_size}")

    ind2lab = label_encoder.ind2lab
    vocab_list = [ind2lab[x] for x in range(len(ind2lab))]

    from speechbrain.decoders.ctc import CTCBeamSearcher

    test_searcher = CTCBeamSearcher(
        **hparams["test_beam_search"],
        vocab_list=vocab_list,
    )
    # Use the same beam search config for validation
    valid_searcher = CTCBeamSearcher(
        **hparams["test_beam_search"],
        vocab_list=vocab_list,
    )

    # Trainer initialization
    asr_brain = ASR(
        modules=hparams["modules"],
        hparams=hparams,
        run_opts=run_opts,
        checkpointer=hparams["checkpointer"],
    )
    # Attach searchers to brain
    asr_brain.valid_searcher = valid_searcher

    # We load the pretrained wav2vec2 model
    if "pretrainer" in hparams.keys():
        hparams["pretrainer"].collect_files()
        hparams["pretrainer"].load_collected()

    # We dynamically add the tokenizer to our brain class.
    # NB: This tokenizer corresponds to the one used for the LM!!
    asr_brain.tokenizer = label_encoder

    # Training
    print("="*60)
    print("STARTING MONICA VOICE FINE-TUNING")
    print("="*60)
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(valid_data)}")
    print(f"Vocabulary size: {actual_vocab_size} characters")
    print(f"Vocabulary: {vocab_list}")
    print(f"Epochs: {hparams['number_of_epochs']}")
    print(f"Batch size: {hparams['batch_size']}")
    print(f"Learning rate (model): {hparams['lr']}")
    print(f"Learning rate (wav2vec): {hparams['lr_wav2vec']}")
    print(f"Freeze wav2vec: {hparams['freeze_wav2vec']}")

    # Early stopping info
    if hasattr(hparams, 'early_stopping_enabled') and hparams['early_stopping_enabled']:
        print(f"Early stopping: ENABLED (patience={hparams['early_stopping_patience']} epochs)")
        print(f"Early stopping metric: {hparams['early_stopping_metric']}")
    else:
        print("Early stopping: DISABLED")

    print("="*60)

    # Run training with early stopping support
    try:
        asr_brain.fit(
            asr_brain.hparams.epoch_counter,
            train_data,
            valid_data,
            train_loader_kwargs=hparams["train_dataloader_opts"],
            valid_loader_kwargs=hparams["valid_dataloader_opts"],
        )
    except StopIteration as e:
        # Early stopping triggered
        print("\n" + "="*60)
        print("EARLY STOPPING TRIGGERED")
        print("="*60)
        print(f"Reason: {e}")
        print(f"Training stopped at epoch {asr_brain.hparams.epoch_counter.current}")
        print(f"Best model already saved (lowest WER)")
        print("="*60 + "\n")

    # Testing
    if not os.path.exists(hparams["output_wer_folder"]):
        os.makedirs(hparams["output_wer_folder"])

    for k in test_datasets.keys():  # keys are val etc
        asr_brain.hparams.test_wer_file = os.path.join(
            hparams["output_wer_folder"], f"wer_{k}.txt"
        )
        asr_brain.evaluate(
            test_datasets[k],
            test_loader_kwargs=hparams["test_dataloader_opts"],
            min_key="WER",
        )

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Model saved to: {hparams['save_folder']}")
    print(f"Logs saved to: {hparams['train_log']}")
    print("="*60)
