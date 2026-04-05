"""
Array Data Structure Visualization
Explains arrays, indexing, and operations
"""

from manim import *

class ArrayBasics(Scene):
    """
    Introduction to arrays and indexing.
    """
    
    def construct(self):
        # Title
        title = Text("Array Data Structure", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create array
        array_values = [10, 20, 30, 40, 50]
        
        # Create boxes
        boxes = VGroup()
        values = VGroup()
        indices = VGroup()
        
        for i, val in enumerate(array_values):
            # Box
            box = Rectangle(height=1.2, width=1.5, color=WHITE, fill_opacity=0.2)
            
            # Value
            value_text = Text(str(val), font_size=36, color=YELLOW)
            value_text.move_to(box.get_center())
            
            # Index
            index_text = Text(str(i), font_size=24, color=GREEN)
            index_text.next_to(box, UP, buff=0.2)
            
            boxes.add(box)
            values.add(value_text)
            indices.add(index_text)
        
        boxes.arrange(RIGHT, buff=0.1)
        boxes.move_to(ORIGIN)
        
        for i, (val, idx) in enumerate(zip(values, indices)):
            val.move_to(boxes[i].get_center())
            idx.next_to(boxes[i], UP, buff=0.2)
        
        # Show array
        self.play(Create(boxes))
        self.play(Write(values))
        self.wait(1)
        
        # Show indices
        index_label = Text("Indices:", font_size=28, color=GREEN)
        index_label.next_to(boxes, UP, buff=1.5).shift(LEFT * 3)
        self.play(Write(index_label))
        self.play(Write(indices))
        self.wait(1)
        
        # Explain indexing
        explanation = Text("Arrays use zero-based indexing", font_size=28, color=YELLOW)
        explanation.to_edge(DOWN, buff=1)
        self.play(Write(explanation))
        self.wait(1)
        
        # Highlight first element
        self.play(
            boxes[0].animate.set_color(RED),
            values[0].animate.set_color(RED),
            indices[0].animate.set_color(RED).scale(1.5)
        )
        
        access_text = Text("array[0] = 10", font_size=32, color=RED)
        access_text.next_to(boxes, DOWN, buff=1)
        self.play(Write(access_text))
        self.wait(1)
        
        # Reset and show another
        self.play(
            boxes[0].animate.set_color(WHITE),
            values[0].animate.set_color(YELLOW),
            indices[0].animate.set_color(GREEN).scale(1/1.5),
            FadeOut(access_text)
        )
        
        # Highlight last element
        self.play(
            boxes[4].animate.set_color(RED),
            values[4].animate.set_color(RED),
            indices[4].animate.set_color(RED).scale(1.5)
        )
        
        access_text2 = Text("array[4] = 50", font_size=32, color=RED)
        access_text2.next_to(boxes, DOWN, buff=1)
        self.play(Write(access_text2))
        self.wait(2)


class ArrayOperations(Scene):
    """
    Show common array operations.
    """
    
    def construct(self):
        title = Text("Array Operations", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Initial array
        array_values = [10, 20, 30]
        boxes, values = self._create_array(array_values)
        
        array_group = VGroup(boxes, values)
        array_group.move_to(ORIGIN + UP)
        
        self.play(Create(boxes), Write(values))
        self.wait(1)
        
        # Operation 1: Append
        op1 = Text("Operation: Append(40)", font_size=32, color=YELLOW)
        op1.to_edge(DOWN, buff=1)
        self.play(Write(op1))
        
        # Create new box
        new_box = Rectangle(height=1.2, width=1.5, color=WHITE, fill_opacity=0.2)
        new_value = Text("40", font_size=36, color=YELLOW)
        new_box.next_to(boxes[-1], RIGHT, buff=0.1)
        new_value.move_to(new_box.get_center())
        
        self.play(Create(new_box), Write(new_value))
        boxes.add(new_box)
        values.add(new_value)
        array_values.append(40)
        self.wait(1)
        
        self.play(FadeOut(op1))
        
        # Operation 2: Insert at index
        op2 = Text("Operation: Insert(25, index=2)", font_size=32, color=YELLOW)
        op2.to_edge(DOWN, buff=1)
        self.play(Write(op2))
        
        # Shift elements right
        self.play(
            boxes[2].animate.shift(RIGHT * 1.6),
            values[2].animate.shift(RIGHT * 1.6),
            boxes[3].animate.shift(RIGHT * 1.6),
            values[3].animate.shift(RIGHT * 1.6)
        )
        
        # Insert new element
        insert_box = Rectangle(height=1.2, width=1.5, color=GREEN, fill_opacity=0.3)
        insert_value = Text("25", font_size=36, color=GREEN)
        insert_box.move_to(boxes[1].get_center() + RIGHT * 1.6)
        insert_value.move_to(insert_box.get_center())
        
        self.play(Create(insert_box), Write(insert_value))
        self.wait(2)
        
        # Show time complexity
        self.play(FadeOut(op2))
        complexity = Text("Time Complexity: O(n) for insert", font_size=28, color=RED)
        complexity.to_edge(DOWN, buff=1)
        self.play(Write(complexity))
        self.wait(2)
    
    def _create_array(self, values):
        boxes = VGroup()
        value_texts = VGroup()
        
        for val in values:
            box = Rectangle(height=1.2, width=1.5, color=WHITE, fill_opacity=0.2)
            value_text = Text(str(val), font_size=36, color=YELLOW)
            
            boxes.add(box)
            value_texts.add(value_text)
        
        boxes.arrange(RIGHT, buff=0.1)
        
        for i, val_text in enumerate(value_texts):
            val_text.move_to(boxes[i].get_center())
        
        return boxes, value_texts


class ArrayVsList(Scene):
    """
    Compare arrays with linked lists.
    """
    
    def construct(self):
        title = Text("Array vs Linked List", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Array advantages
        array_title = Text("Array", font_size=32, color=GREEN)
        array_title.shift(UP * 1.5 + LEFT * 3)
        
        array_pros = VGroup(
            Text("✓ Fast random access O(1)", font_size=24, color=GREEN),
            Text("✓ Cache-friendly", font_size=24, color=GREEN),
            Text("✗ Fixed size", font_size=24, color=RED),
            Text("✗ Slow insert/delete O(n)", font_size=24, color=RED)
        )
        array_pros.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        array_pros.next_to(array_title, DOWN, buff=0.5)
        
        # Linked list advantages
        list_title = Text("Linked List", font_size=32, color=YELLOW)
        list_title.shift(UP * 1.5 + RIGHT * 3)
        
        list_pros = VGroup(
            Text("✓ Dynamic size", font_size=24, color=GREEN),
            Text("✓ Fast insert/delete O(1)", font_size=24, color=GREEN),
            Text("✗ Slow access O(n)", font_size=24, color=RED),
            Text("✗ Extra memory", font_size=24, color=RED)
        )
        list_pros.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        list_pros.next_to(list_title, DOWN, buff=0.5)
        
        self.play(Write(array_title), Write(list_title))
        self.wait(0.5)
        
        for ap, lp in zip(array_pros, list_pros):
            self.play(Write(ap), Write(lp))
            self.wait(0.3)
        
        self.wait(2)
