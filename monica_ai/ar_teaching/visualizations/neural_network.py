"""
Neural Network Visualization
Shows network architecture and forward propagation
"""

from manim import *
import numpy as np

class NeuralNetworkBasics(Scene):
    """
    Introduction to neural network architecture.
    """
    
    def construct(self):
        # Title
        title = Text("Neural Network", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create layers
        input_layer = self._create_layer(3, "Input\nLayer", LEFT * 4)
        hidden_layer = self._create_layer(4, "Hidden\nLayer", ORIGIN)
        output_layer = self._create_layer(2, "Output\nLayer", RIGHT * 4)
        
        # Show layers
        self.play(Create(input_layer[0]), Write(input_layer[1]))
        self.wait(0.5)
        self.play(Create(hidden_layer[0]), Write(hidden_layer[1]))
        self.wait(0.5)
        self.play(Create(output_layer[0]), Write(output_layer[1]))
        self.wait(1)
        
        # Create connections
        connections = VGroup()
        
        # Input to hidden
        for i_neuron in input_layer[0]:
            for h_neuron in hidden_layer[0]:
                line = Line(
                    i_neuron.get_center(),
                    h_neuron.get_center(),
                    stroke_width=1,
                    stroke_opacity=0.3,
                    color=GRAY
                )
                connections.add(line)
        
        # Hidden to output
        for h_neuron in hidden_layer[0]:
            for o_neuron in output_layer[0]:
                line = Line(
                    h_neuron.get_center(),
                    o_neuron.get_center(),
                    stroke_width=1,
                    stroke_opacity=0.3,
                    color=GRAY
                )
                connections.add(line)
        
        self.play(Create(connections), run_time=2)
        self.wait(1)
        
        # Explanation
        explanation = Text(
            "Each connection has a weight (learned parameter)",
            font_size=28,
            color=YELLOW
        )
        explanation.to_edge(DOWN, buff=1)
        self.play(Write(explanation))
        self.wait(2)
    
    def _create_layer(self, num_neurons, label, position):
        """Create a layer of neurons."""
        neurons = VGroup()
        
        for i in range(num_neurons):
            neuron = Circle(radius=0.3, color=WHITE, fill_opacity=0.5)
            neurons.add(neuron)
        
        neurons.arrange(DOWN, buff=0.5)
        neurons.move_to(position)
        
        # Label
        label_text = Text(label, font_size=24, color=YELLOW)
        label_text.next_to(neurons, DOWN, buff=0.5)
        
        return neurons, label_text


class ForwardPropagation(Scene):
    """
    Demonstrate forward propagation through network.
    """
    
    def construct(self):
        title = Text("Forward Propagation", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create simple network: 2 -> 3 -> 1
        input_layer = self._create_layer(2, LEFT * 4)
        hidden_layer = self._create_layer(3, ORIGIN)
        output_layer = self._create_layer(1, RIGHT * 4)
        
        self.play(
            Create(input_layer),
            Create(hidden_layer),
            Create(output_layer)
        )
        
        # Create connections
        connections = self._create_connections(
            [input_layer, hidden_layer, output_layer]
        )
        self.play(Create(connections))
        self.wait(1)
        
        # Show input values
        input_values = [0.5, 0.8]
        for i, (neuron, val) in enumerate(zip(input_layer, input_values)):
            value_text = Text(f"{val}", font_size=20, color=GREEN)
            value_text.next_to(neuron, LEFT, buff=0.3)
            self.play(Write(value_text))
            neuron.set_fill(GREEN, opacity=val)
        
        self.wait(1)
        
        # Animate signal propagation
        explanation = Text("Signal flows forward through network", font_size=28, color=YELLOW)
        explanation.to_edge(DOWN, buff=1)
        self.play(Write(explanation))
        
        # Propagate to hidden layer
        for h_neuron in hidden_layer:
            # Simulate activation
            activation = np.random.random()
            self.play(h_neuron.animate.set_fill(BLUE, opacity=activation), run_time=0.3)
        
        self.wait(0.5)
        
        # Propagate to output
        for o_neuron in output_layer:
            activation = np.random.random()
            self.play(o_neuron.animate.set_fill(RED, opacity=activation), run_time=0.3)
        
        self.wait(1)
        
        # Show output
        output_text = Text("Output: 0.73", font_size=32, color=RED)
        output_text.next_to(output_layer[0], RIGHT, buff=0.5)
        self.play(Write(output_text))
        self.wait(2)
    
    def _create_layer(self, num_neurons, position):
        neurons = VGroup()
        for i in range(num_neurons):
            neuron = Circle(radius=0.3, color=WHITE, fill_opacity=0.2)
            neurons.add(neuron)
        neurons.arrange(DOWN, buff=0.5)
        neurons.move_to(position)
        return neurons
    
    def _create_connections(self, layers):
        connections = VGroup()
        for i in range(len(layers) - 1):
            for n1 in layers[i]:
                for n2 in layers[i + 1]:
                    line = Line(
                        n1.get_center(),
                        n2.get_center(),
                        stroke_width=1,
                        stroke_opacity=0.2,
                        color=GRAY
                    )
                    connections.add(line)
        return connections


class ActivationFunctions(Scene):
    """
    Show common activation functions.
    """
    
    def construct(self):
        title = Text("Activation Functions", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1.5, 1.5, 0.5],
            x_length=6,
            y_length=4,
            axis_config={"color": WHITE}
        )
        axes.move_to(ORIGIN)
        
        # Labels
        x_label = axes.get_x_axis_label("x")
        y_label = axes.get_y_axis_label("f(x)")
        
        self.play(Create(axes), Write(x_label), Write(y_label))
        
        # Sigmoid function
        sigmoid_label = Text("Sigmoid: σ(x) = 1/(1+e^-x)", font_size=24, color=YELLOW)
        sigmoid_label.to_edge(DOWN, buff=1)
        self.play(Write(sigmoid_label))
        
        sigmoid = axes.plot(
            lambda x: 1 / (1 + np.exp(-x)),
            color=YELLOW,
            x_range=[-3, 3]
        )
        self.play(Create(sigmoid))
        self.wait(2)
        
        # ReLU function
        self.play(FadeOut(sigmoid), FadeOut(sigmoid_label))
        
        relu_label = Text("ReLU: f(x) = max(0, x)", font_size=24, color=GREEN)
        relu_label.to_edge(DOWN, buff=1)
        self.play(Write(relu_label))
        
        relu = axes.plot(
            lambda x: max(0, x),
            color=GREEN,
            x_range=[-3, 3]
        )
        self.play(Create(relu))
        self.wait(2)
        
        # Tanh function
        self.play(FadeOut(relu), FadeOut(relu_label))
        
        tanh_label = Text("Tanh: f(x) = (e^x - e^-x)/(e^x + e^-x)", font_size=24, color=RED)
        tanh_label.to_edge(DOWN, buff=1)
        self.play(Write(tanh_label))
        
        tanh = axes.plot(
            lambda x: np.tanh(x),
            color=RED,
            x_range=[-3, 3]
        )
        self.play(Create(tanh))
        self.wait(2)


class BackpropagationIntro(Scene):
    """
    Introduction to backpropagation.
    """
    
    def construct(self):
        title = Text("Backpropagation", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create network
        input_layer = self._create_layer(2, LEFT * 4)
        hidden_layer = self._create_layer(3, ORIGIN)
        output_layer = self._create_layer(1, RIGHT * 4)
        
        self.play(
            Create(input_layer),
            Create(hidden_layer),
            Create(output_layer)
        )
        
        connections = self._create_connections([input_layer, hidden_layer, output_layer])
        self.play(Create(connections))
        self.wait(1)
        
        # Show forward pass
        forward_text = Text("1. Forward Pass", font_size=28, color=GREEN)
        forward_text.to_edge(DOWN, buff=2)
        self.play(Write(forward_text))
        
        # Animate forward
        for layer in [input_layer, hidden_layer, output_layer]:
            for neuron in layer:
                self.play(neuron.animate.set_fill(GREEN, opacity=0.5), run_time=0.2)
        
        self.wait(1)
        
        # Show error
        error_text = Text("2. Calculate Error", font_size=28, color=RED)
        error_text.next_to(forward_text, DOWN, buff=0.3)
        self.play(Write(error_text))
        
        self.play(output_layer[0].animate.set_fill(RED, opacity=0.8))
        self.wait(1)
        
        # Show backward pass
        backward_text = Text("3. Backward Pass (Update Weights)", font_size=28, color=YELLOW)
        backward_text.next_to(error_text, DOWN, buff=0.3)
        self.play(Write(backward_text))
        
        # Animate backward
        for layer in [output_layer, hidden_layer, input_layer]:
            for neuron in layer:
                self.play(neuron.animate.set_fill(YELLOW, opacity=0.5), run_time=0.2)
        
        self.wait(2)
    
    def _create_layer(self, num_neurons, position):
        neurons = VGroup()
        for i in range(num_neurons):
            neuron = Circle(radius=0.3, color=WHITE, fill_opacity=0.2)
            neurons.add(neuron)
        neurons.arrange(DOWN, buff=0.5)
        neurons.move_to(position)
        return neurons
    
    def _create_connections(self, layers):
        connections = VGroup()
        for i in range(len(layers) - 1):
            for n1 in layers[i]:
                for n2 in layers[i + 1]:
                    line = Line(n1.get_center(), n2.get_center(),
                               stroke_width=1, stroke_opacity=0.2, color=GRAY)
                    connections.add(line)
        return connections
