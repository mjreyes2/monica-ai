"""
Bubble Sort Algorithm Visualization
Step-by-step animated explanation using Manim
"""

from manim import *

class BubbleSortVisualization(Scene):
    """
    Visual explanation of bubble sort algorithm.
    Shows how elements "bubble up" to their correct positions.
    """
    
    def construct(self):
        # Title
        title = Text("Bubble Sort Algorithm", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Initial array
        array_values = [5, 2, 8, 1, 9]
        
        # Create bars for visualization
        bars = VGroup()
        labels = VGroup()
        
        for i, val in enumerate(array_values):
            bar = Rectangle(
                height=val * 0.5,
                width=0.8,
                fill_opacity=0.8,
                fill_color=BLUE,
                stroke_color=WHITE
            )
            label = Text(str(val), font_size=28)
            label.next_to(bar, DOWN, buff=0.2)
            
            bars.add(bar)
            labels.add(label)
        
        # Arrange bars
        bars.arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        bars.move_to(ORIGIN)
        
        # Position labels
        for i, label in enumerate(labels):
            label.next_to(bars[i], DOWN, buff=0.2)
        
        self.play(Create(bars), Write(labels))
        self.wait(1)
        
        # Show algorithm description
        desc = Text("Compare adjacent elements and swap if needed", font_size=24, color=YELLOW)
        desc.to_edge(DOWN, buff=1)
        self.play(Write(desc))
        self.wait(1)
        
        # Bubble sort algorithm
        n = len(array_values)
        swaps = 0
        
        for i in range(n):
            for j in range(0, n - i - 1):
                # Highlight comparison
                self.play(
                    bars[j].animate.set_color(RED),
                    bars[j + 1].animate.set_color(RED)
                )
                self.wait(0.3)
                
                # Compare
                if array_values[j] > array_values[j + 1]:
                    # Swap animation
                    swaps += 1
                    
                    # Show swap
                    swap_text = Text("SWAP", font_size=32, color=YELLOW)
                    swap_text.move_to(bars[j].get_center() + UP * 2)
                    self.play(Write(swap_text))
                    
                    # Animate swap
                    self.play(
                        bars[j].animate.shift(RIGHT * 1.1),
                        bars[j + 1].animate.shift(LEFT * 1.1),
                        labels[j].animate.shift(RIGHT * 1.1),
                        labels[j + 1].animate.shift(LEFT * 1.1)
                    )
                    
                    # Swap in arrays
                    bars[j], bars[j + 1] = bars[j + 1], bars[j]
                    labels[j], labels[j + 1] = labels[j + 1], labels[j]
                    array_values[j], array_values[j + 1] = array_values[j + 1], array_values[j]
                    
                    self.play(FadeOut(swap_text))
                    self.wait(0.3)
                
                # Reset colors
                self.play(
                    bars[j].animate.set_color(BLUE),
                    bars[j + 1].animate.set_color(BLUE)
                )
            
            # Mark sorted element
            self.play(bars[n - i - 1].animate.set_color(GREEN))
            self.wait(0.3)
        
        # Final result
        self.play(FadeOut(desc))
        result = Text(f"Sorted! ({swaps} swaps)", font_size=36, color=GREEN)
        result.to_edge(DOWN, buff=1)
        self.play(Write(result))
        self.wait(2)


class BubbleSortComplexity(Scene):
    """
    Explain time complexity of bubble sort.
    """
    
    def construct(self):
        title = Text("Bubble Sort Complexity", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Time complexity
        time_complexity = MathTex(r"O(n^2)", font_size=72, color=RED)
        time_complexity.move_to(ORIGIN)
        self.play(Write(time_complexity))
        self.wait(1)
        
        # Explanation
        explanation = VGroup(
            Text("Best Case: O(n) - already sorted", font_size=28, color=GREEN),
            Text("Average Case: O(n²)", font_size=28, color=YELLOW),
            Text("Worst Case: O(n²) - reverse sorted", font_size=28, color=RED)
        )
        explanation.arrange(DOWN, buff=0.5)
        explanation.next_to(time_complexity, DOWN, buff=1)
        
        for line in explanation:
            self.play(Write(line))
            self.wait(0.5)
        
        self.wait(2)
