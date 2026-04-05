using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace MonicaWPF
{
    /// <summary>
    /// Monica AI WPF Frontend — GPU-accelerated UI communicating with Python backend via named pipes.
    /// 
    /// Architecture:
    ///   Python backend ←→ Named Pipe (MonicaPipe) ←→ C# WPF Frontend
    ///   
    /// Pipe protocol (JSON lines, newline-delimited):
    ///   Backend → Frontend:
    ///     {"type":"frame","data":"<base64 JPEG>"}
    ///     {"type":"chat","role":"monica","text":"Hello!"}
    ///     {"type":"status","services":{"stt":"active",...},"emotion":"happy"}
    ///   Frontend → Backend:
    ///     {"type":"command","command":"camera_on"}
    ///     {"type":"chat","text":"user message here"}
    /// </summary>
    public partial class MainWindow : Window
    {
        private const string PIPE_NAME = "MonicaAIPipe";

        private NamedPipeClientStream? _pipeIn;
        private NamedPipeClientStream? _pipeOut;
        private StreamReader? _reader;
        private StreamWriter? _writer;
        private CancellationTokenSource _cts = new();
        private bool _connected = false;
        private bool _cameraOn = false;

        // FPS tracking
        private int _frameCount = 0;
        private DateTime _lastFpsTime = DateTime.Now;
        private WriteableBitmap? _videoBitmap;

        public MainWindow()
        {
            InitializeComponent();
            Loaded += MainWindow_Loaded;
            Closing += MainWindow_Closing;
        }

        private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            AddChatMessage("System", "Monica AI WPF Frontend starting...", "#888888");
            AddChatMessage("System", "Connecting to Python backend via named pipe...", "#888888");
            await ConnectToPythonAsync();
        }

        private void MainWindow_Closing(object? sender, System.ComponentModel.CancelEventArgs e)
        {
            _cts.Cancel();
            _pipeIn?.Dispose();
            _pipeOut?.Dispose();
        }

        // ══════════════════════════════════════════════════════════════
        //  Named Pipe Communication
        // ══════════════════════════════════════════════════════════════

        private async Task ConnectToPythonAsync()
        {
            try
            {
                // Input pipe: receive data from Python
                _pipeIn = new NamedPipeClientStream(".", PIPE_NAME + "_out", PipeDirection.In);
                // Output pipe: send commands to Python
                _pipeOut = new NamedPipeClientStream(".", PIPE_NAME + "_in", PipeDirection.Out);

                // Try connecting with timeout
                var connectTask = Task.WhenAll(
                    _pipeIn.ConnectAsync(5000, _cts.Token),
                    _pipeOut.ConnectAsync(5000, _cts.Token)
                );

                await connectTask;

                _reader = new StreamReader(_pipeIn, Encoding.UTF8);
                _writer = new StreamWriter(_pipeOut, Encoding.UTF8) { AutoFlush = true };
                _connected = true;

                Dispatcher.Invoke(() =>
                {
                    ConnectionDot.Fill = (SolidColorBrush)FindResource("GreenBrush");
                    AddChatMessage("System", "Connected to Monica backend!", "#00ff88");
                });

                // Start reading messages from Python
                _ = Task.Run(() => ReadPipeLoop(_cts.Token));
            }
            catch (TimeoutException)
            {
                Dispatcher.Invoke(() =>
                {
                    AddChatMessage("System",
                        "Could not connect to Python backend. Make sure Monica is running with pipe server enabled.",
                        "#ff4444");
                    AddChatMessage("System",
                        "To enable: set MONICA_PIPE_SERVER=1 in .env or run with --pipe flag",
                        "#888888");
                });
            }
            catch (Exception ex)
            {
                Dispatcher.Invoke(() =>
                {
                    AddChatMessage("System", $"Connection error: {ex.Message}", "#ff4444");
                });
            }
        }

        private async void ReadPipeLoop(CancellationToken ct)
        {
            try
            {
                while (!ct.IsCancellationRequested && _reader != null)
                {
                    var line = await _reader.ReadLineAsync();
                    if (line == null) break;

                    try
                    {
                        var msg = JObject.Parse(line);
                        var type = msg["type"]?.ToString();

                        switch (type)
                        {
                            case "frame":
                                HandleFrame(msg);
                                break;
                            case "chat":
                                HandleChat(msg);
                                break;
                            case "status":
                                HandleStatus(msg);
                                break;
                        }
                    }
                    catch (JsonException)
                    {
                        // Skip malformed messages
                    }
                }
            }
            catch (OperationCanceledException) { }
            catch (IOException) { }
            finally
            {
                Dispatcher.Invoke(() =>
                {
                    _connected = false;
                    ConnectionDot.Fill = (SolidColorBrush)FindResource("RedBrush");
                    AddChatMessage("System", "Disconnected from backend", "#ff4444");
                });
            }
        }

        private async Task SendCommand(string command, JObject? extra = null)
        {
            if (!_connected || _writer == null) return;
            try
            {
                var msg = new JObject
                {
                    ["type"] = "command",
                    ["command"] = command
                };
                if (extra != null)
                {
                    foreach (var prop in extra.Properties())
                        msg[prop.Name] = prop.Value;
                }
                await _writer.WriteLineAsync(msg.ToString(Formatting.None));
            }
            catch (Exception) { }
        }

        private async Task SendChat(string text)
        {
            if (!_connected || _writer == null) return;
            try
            {
                var msg = new JObject
                {
                    ["type"] = "chat",
                    ["text"] = text
                };
                await _writer.WriteLineAsync(msg.ToString(Formatting.None));
            }
            catch (Exception) { }
        }

        // ══════════════════════════════════════════════════════════════
        //  Message Handlers
        // ══════════════════════════════════════════════════════════════

        private void HandleFrame(JObject msg)
        {
            var b64 = msg["data"]?.ToString();
            if (string.IsNullOrEmpty(b64)) return;

            try
            {
                var jpegBytes = Convert.FromBase64String(b64);

                Dispatcher.Invoke(() =>
                {
                    // Decode JPEG to BitmapImage
                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.StreamSource = new MemoryStream(jpegBytes);
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.EndInit();
                    bitmap.Freeze(); // Allow cross-thread access

                    VideoImage.Source = bitmap;
                    CameraOffText.Visibility = Visibility.Collapsed;

                    // FPS counter
                    _frameCount++;
                    var now = DateTime.Now;
                    if ((now - _lastFpsTime).TotalSeconds >= 1.0)
                    {
                        FpsLabel.Text = $"{_frameCount} FPS";
                        _frameCount = 0;
                        _lastFpsTime = now;
                    }
                });
            }
            catch (Exception) { }
        }

        private void HandleChat(JObject msg)
        {
            var role = msg["role"]?.ToString() ?? "system";
            var text = msg["text"]?.ToString() ?? "";

            var color = role switch
            {
                "user" => "#6688ff",
                "monica" => "#00d4ff",
                _ => "#888888"
            };

            var label = role switch
            {
                "user" => "You",
                "monica" => "Monica",
                _ => "System"
            };

            Dispatcher.Invoke(() => AddChatMessage(label, text, color));
        }

        private void HandleStatus(JObject msg)
        {
            Dispatcher.Invoke(() =>
            {
                var services = msg["services"] as JObject;
                if (services != null)
                {
                    UpdateServiceLabel(StatusSTT, "STT", services["stt"]?.ToString());
                    UpdateServiceLabel(StatusTTS, "TTS", services["tts"]?.ToString());
                    UpdateServiceLabel(StatusAI, "AI", services["ai"]?.ToString());
                    UpdateServiceLabel(StatusVision, "Vision", services["vision"]?.ToString());
                }

                var emotion = msg["emotion"]?.ToString();
                if (!string.IsNullOrEmpty(emotion))
                {
                    StatusEmotion.Text = emotion;
                }

                var micEnergy = msg["mic_energy"]?.Value<double>() ?? 0.0;
                var barWidth = Math.Min(80, micEnergy * 2000);
                MicLevelBar.Width = barWidth;
            });
        }

        private void UpdateServiceLabel(TextBlock label, string name, string? state)
        {
            label.Text = $"{name}: {state ?? "--"}";
            label.Foreground = state == "active"
                ? (SolidColorBrush)FindResource("GreenBrush")
                : (SolidColorBrush)FindResource("DimTextBrush");
        }

        // ══════════════════════════════════════════════════════════════
        //  UI Helpers
        // ══════════════════════════════════════════════════════════════

        private void AddChatMessage(string label, string text, string colorHex)
        {
            var border = new Border
            {
                Background = new SolidColorBrush(
                    (Color)ColorConverter.ConvertFromString("#20" + colorHex.TrimStart('#'))),
                BorderBrush = new SolidColorBrush(
                    (Color)ColorConverter.ConvertFromString("#30" + colorHex.TrimStart('#'))),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(8, 4, 8, 4),
                Margin = new Thickness(0, 2, 0, 2),
            };

            var stack = new StackPanel { Orientation = Orientation.Horizontal };

            stack.Children.Add(new TextBlock
            {
                Text = label + ": ",
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(colorHex)),
                FontWeight = FontWeights.SemiBold,
                FontSize = 12,
                FontFamily = new FontFamily("Segoe UI"),
            });

            stack.Children.Add(new TextBlock
            {
                Text = text,
                Foreground = (SolidColorBrush)FindResource("TextBrush"),
                FontSize = 12,
                FontFamily = new FontFamily("Segoe UI"),
                TextWrapping = TextWrapping.Wrap,
            });

            border.Child = stack;
            ChatMessages.Children.Add(border);

            // Auto-scroll
            ChatScroll.ScrollToEnd();

            // Limit history
            while (ChatMessages.Children.Count > 200)
                ChatMessages.Children.RemoveAt(0);
        }

        // ══════════════════════════════════════════════════════════════
        //  Button Handlers
        // ══════════════════════════════════════════════════════════════

        private async void CameraBtn_Click(object sender, RoutedEventArgs e)
        {
            _cameraOn = !_cameraOn;
            CameraBtn.Content = _cameraOn ? "Stop Camera" : "Start Camera";
            CameraOffText.Visibility = _cameraOn ? Visibility.Collapsed : Visibility.Visible;
            await SendCommand(_cameraOn ? "camera_on" : "camera_off");
        }

        private async void GlobeBtn_Click(object sender, RoutedEventArgs e)
        {
            await SendCommand("toggle_globe");
        }

        private async void InitBtn_Click(object sender, RoutedEventArgs e)
        {
            await SendCommand("initialize");
            AddChatMessage("System", "Initializing Monica...", "#00d4ff");
        }

        private async void SpoutBtn_Click(object sender, RoutedEventArgs e)
        {
            await SendCommand("toggle_spout");
        }

        private async void VoiceBtn_Click(object sender, RoutedEventArgs e)
        {
            var current = VoiceBtn.Content?.ToString() ?? "";
            if (current.Contains("ON"))
            {
                VoiceBtn.Content = "Voice: OFF";
                await SendCommand("set_stt_mode", new JObject { ["mode"] = "off" });
            }
            else
            {
                VoiceBtn.Content = "Voice: ON";
                await SendCommand("set_stt_mode", new JObject { ["mode"] = "hands_free" });
            }
        }

        private async void SendBtn_Click(object sender, RoutedEventArgs e)
        {
            await SendChatInput();
        }

        private async void ChatInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                e.Handled = true;
                await SendChatInput();
            }
        }

        private async Task SendChatInput()
        {
            var text = ChatInput.Text.Trim();
            if (string.IsNullOrEmpty(text)) return;

            AddChatMessage("You", text, "#6688ff");
            ChatInput.Text = "";
            await SendChat(text);
        }
    }
}
