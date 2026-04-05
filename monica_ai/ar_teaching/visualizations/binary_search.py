"""
Binary Search Algorithm Visualization
Step-by-step animated explanation using Manim
"""

from manim import *

class BinarySearchVisualization(Scene):
    """
    Visual explanation of binary search algorithm.
    Shows how binary search efficiently finds a target in a sorted array.
    """
    
    def construct(self):
        # Title
        title = Text("Binary Search Algorithm", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Step 1: Show sorted array
        subtitle1 = Text("Step 1: Start with a sorted array", font_size=32, color=YELLOW)
        subtitle1.next_to(title, DOWN, buff=0.5)
        self.play(Write(subtitle1))
        
        # Create array visualization
        array_values = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        target = 13
        
        # Create boxes for array elements
        boxes = VGroup()
        labels = VGroup()
        
        for i, val in enumerate(array_values):
            box = Rectangle(height=1, width=1, color=WHITE)
            label = Text(str(val), font_size=32)
            
            boxes.add(box)
            labels.add(label)
        
        boxes.arrange(RIGHT, buff=0.1)
        boxes.move_to(ORIGIN)
        
        # Position labels inside boxes
        for i, (box, label) in enumerate(zip(boxes, labels)):
            label.move_to(box.get_center())
        
        self.play(Create(boxes), Write(labels))
        self.wait(1)
        
        # Show target
        target_text = Text(f"Target: {target}", font_size=36, color=GREEN)
        target_text.to_edge(DOWN, buff=1)
        self.play(Write(target_text))
        self.wait(1)
        
        # Remove subtitle
        self.play(FadeOut(subtitle1))
        
        # Step 2: Show search process
        subtitle2 = Text("Step 2: Check middle element", font_size=32, color=YELLOW)
        subtitle2.next_to(title, DOWN, buff=0.5)
        self.play(Write(subtitle2))
        
        # Pointers
        left = 0
        right = len(array_values) - 1
        
        # Create pointer indicators
        left_arrow = Arrow(start=UP, end=DOWN, color=RED).scale(0.5)
        right_arrow = Arrow(start=UP, end=DOWN, color=RED).scale(0.5)
        mid_arrow = Arrow(start=UP, end=DOWN, color=YELLOW).scale(0.5)
        
        left_arrow.next_to(boxes[left], UP, buff=0.2)
        right_arrow.next_to(boxes[right], UP, buff=0.2)
        
        left_label = Text("L", font_size=24, color=RED).next_to(left_arrow, UP, buff=0.1)
        right_label = Text("R", font_size=24, color=RED).next_to(right_arrow, UP, buff=0.1)
        
        self.play(GrowArrow(left_arrow), Write(left_label))
        self.play(GrowArrow(right_arrow), Write(right_label))
        self.wait(1)
        
        # Binary search iterations
        iteration = 1
        while left <= right:
            mid = (left + right) // 2
            
            # Show middle pointer
            mid_arrow.next_to(boxes[mid], UP, buff=0.2)
            mid_label = Text("M", font_size=24, color=YELLOW).next_to(mid_arrow, UP, buff=0.1)
            
            self.play(GrowArrow(mid_arrow), Write(mid_label))
            
            # Highlight middle element
            self.play(boxes[mid].animate.set_color(YELLOW))
            self.wait(0.5)
            
            # Compare with target
            comparison = Text(
                f"{array_values[mid]} {'=' if array_values[mid] == target else '<' if array_values[mid] < target else '>'} {target}",
                font_size=28,
                color=YELLOW
            )
            comparison.next_to(boxes[mid], DOWN, buff=0.5)
            self.play(Write(comparison))
            self.wait(1)
            
            if array_values[mid] == target:
                # Found!
                self.play(FadeOut(subtitle2))
                found_text = Text("FOUND!", font_size=48, color=GREEN)
                found_text.next_to(title, DOWN, buff=0.5)
                self.play(Write(found_text))
                
                # Highlight found element
                self.play(
                    boxes[mid].animate.set_color(GREEN).scale(1.2),
                    labels[mid].animate.set_color(GREEN).scale(1.2)
                )
                self.wait(2)
                break
            
            elif array_values[mid] < target:
                # Search right half
                self.play(FadeOut(comparison))
                
                # Fade out left half
                fade_boxes = VGroup(*[boxes[i] for i in range(left, mid + 1)])
                fade_labels = VGroup(*[labels[i] for i in range(left, mid + 1)])
                self.play(
                    fade_boxes.animate.set_opacity(0.3),
                    fade_labels.animate.set_opacity(0.3)
                )
                
                # Update pointers
                left = mid + 1
                self.play(
                    left_arrow.animate.next_to(boxes[left], UP, buff=0.2),
                    left_label.animate.next_to(boxes[left], UP, buff=0.7),
                    FadeOut(mid_arrow),
                    FadeOut(mid_label)
                )
                
            else:
                # Search left half
                self.play(FadeOut(comparison))
                
                # Fade out right half
                fade_boxes = VGroup(*[boxes[i] for i in range(mid, right + 1)])
                fade_labels = VGroup(*[labels[i] for i in range(mid, right + 1)])
                self.play(
                    fade_boxes.animate.set_opacity(0.3),
                    fade_labels.animate.set_opacity(0.3)
                )
                
                # Update pointers
                right = mid - 1
                self.play(
                    right_arrow.animate.next_to(boxes[right], UP, buff=0.2),
                    right_label.animate.next_to(boxes[right], UP, buff=0.7),
                    FadeOut(mid_arrow),
                    FadeOut(mid_label)
                )
            
            self.wait(0.5)
            iteration += 1
        
        # Summary
        self.wait(1)
        summary = Text(
            f"Binary Search: O(log n) - Found in {iteration} steps",
            font_size=32,
            color=BLUE
        )
        summary.to_edge(DOWN, buff=0.5)
        self.play(Write(summary))
        self.wait(2)


class BinarySearchComparison(Scene):
    """
    Compare binary search with linear search.
    Shows efficiency difference.
    """
    
    def construct(self):
        title = Text("Binary Search vs Linear Search", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create comparison
        linear_text = Text("Linear Search: O(n)", font_size=32, color=RED)
        binary_text = Text("Binary Search: O(log n)", font_size=32, color=GREEN)
        
        linear_text.shift(UP * 1)
        binary_text.shift(DOWN * 1)
        
        self.play(Write(linear_text))
        self.play(Write(binary_text))
        
        # Show example with n=1000
        example = Text("For 1000 elements:", font_size=28, color=YELLOW)
        example.shift(DOWN * 2.5)
        
        linear_steps = Text("Linear: ~1000 steps", font_size=24, color=RED)
        binary_steps = Text("Binary: ~10 steps", font_size=24, color=GREEN)
        
        linear_steps.next_to(example, DOWN, buff=0.3).shift(LEFT * 2)
        binary_steps.next_to(example, DOWN, buff=0.3).shift(RIGHT * 2)
        
        self.play(Write(example))
        self.wait(0.5)
        self.play(Write(linear_steps))
        self.play(Write(binary_steps))
        
        # Highlight efficiency
        efficiency = Text("100x faster!", font_size=36, color=GREEN, weight=BOLD)
        efficiency.to_edge(DOWN, buff=1)
        self.play(Write(efficiency))
        
        self.wait(3)
