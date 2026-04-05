"""
Linked List Data Structure Visualization
Shows nodes, pointers, and operations
"""

from manim import *

class LinkedListBasics(Scene):
    """
    Introduction to linked lists.
    """
    
    def construct(self):
        # Title
        title = Text("Linked List Data Structure", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create first node
        node1 = self._create_node(10)
        node1.move_to(LEFT * 4 + UP * 0.5)
        
        self.play(Create(node1))
        self.wait(0.5)
        
        # Add label
        label1 = Text("Node", font_size=24, color=YELLOW)
        label1.next_to(node1, DOWN, buff=0.5)
        self.play(Write(label1))
        self.wait(1)
        
        # Create second node
        node2 = self._create_node(20)
        node2.move_to(RIGHT * 0 + UP * 0.5)
        
        self.play(Create(node2))
        self.wait(0.5)
        
        # Create pointer arrow
        arrow1 = Arrow(
            start=node1.get_right() + RIGHT * 0.1,
            end=node2.get_left() + LEFT * 0.1,
            color=GREEN,
            buff=0.1
        )
        
        pointer_label = Text("Pointer", font_size=20, color=GREEN)
        pointer_label.next_to(arrow1, UP, buff=0.1)
        
        self.play(GrowArrow(arrow1), Write(pointer_label))
        self.wait(1)
        
        # Create third node
        node3 = self._create_node(30)
        node3.move_to(RIGHT * 4 + UP * 0.5)
        
        self.play(Create(node3))
        
        arrow2 = Arrow(
            start=node2.get_right() + RIGHT * 0.1,
            end=node3.get_left() + LEFT * 0.1,
            color=GREEN,
            buff=0.1
        )
        
        self.play(GrowArrow(arrow2))
        self.wait(1)
        
        # Show NULL pointer
        null_text = Text("NULL", font_size=24, color=RED)
        null_text.next_to(node3, RIGHT, buff=0.5)
        
        arrow3 = Arrow(
            start=node3.get_right() + RIGHT * 0.1,
            end=null_text.get_left() + LEFT * 0.1,
            color=RED,
            buff=0.1
        )
        
        self.play(GrowArrow(arrow3), Write(null_text))
        self.wait(1)
        
        # Explanation
        explanation = Text(
            "Each node contains data and a pointer to the next node",
            font_size=28,
            color=YELLOW
        )
        explanation.to_edge(DOWN, buff=1)
        self.play(Write(explanation))
        self.wait(2)
    
    def _create_node(self, value):
        """Create a linked list node visualization."""
        # Node box
        box = Rectangle(height=1, width=2, color=WHITE, fill_opacity=0.2)
        
        # Value
        value_text = Text(str(value), font_size=32, color=YELLOW)
        value_text.move_to(box.get_center() + LEFT * 0.4)
        
        # Pointer box
        pointer_box = Rectangle(height=1, width=0.6, color=GREEN, fill_opacity=0.1)
        pointer_box.next_to(box, RIGHT, buff=0)
        pointer_box.align_to(box, UP)
        
        return VGroup(box, value_text, pointer_box)


class LinkedListInsertion(Scene):
    """
    Show insertion operation in linked list.
    """
    
    def construct(self):
        title = Text("Linked List: Insert Operation", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create initial list: 10 -> 20 -> 30
        nodes = []
        arrows = []
        
        for i, val in enumerate([10, 20, 30]):
            node = self._create_node(val)
            node.move_to(LEFT * 4 + RIGHT * i * 3.5 + UP * 0.5)
            nodes.append(node)
            self.play(Create(node), run_time=0.5)
            
            if i > 0:
                arrow = Arrow(
                    start=nodes[i-1].get_right() + RIGHT * 0.1,
                    end=nodes[i].get_left() + LEFT * 0.1,
                    color=GREEN,
                    buff=0.1
                )
                arrows.append(arrow)
                self.play(GrowArrow(arrow), run_time=0.5)
        
        self.wait(1)
        
        # Insert 15 between 10 and 20
        operation = Text("Insert 15 after 10", font_size=32, color=YELLOW)
        operation.to_edge(DOWN, buff=1)
        self.play(Write(operation))
        self.wait(1)
        
        # Create new node
        new_node = self._create_node(15)
        new_node.move_to(nodes[0].get_center() + DOWN * 2)
        new_node.set_color(RED)
        
        self.play(Create(new_node))
        self.wait(0.5)
        
        # Step 1: Point new node to node 20
        step1 = Text("Step 1: new_node.next = node2", font_size=24, color=YELLOW)
        step1.next_to(operation, UP, buff=0.3)
        self.play(Write(step1))
        
        new_arrow1 = Arrow(
            start=new_node.get_right() + RIGHT * 0.1,
            end=nodes[1].get_bottom() + DOWN * 0.1,
            color=RED,
            buff=0.1
        )
        self.play(GrowArrow(new_arrow1))
        self.wait(1)
        
        # Step 2: Point node 10 to new node
        self.play(FadeOut(step1))
        step2 = Text("Step 2: node1.next = new_node", font_size=24, color=YELLOW)
        step2.next_to(operation, UP, buff=0.3)
        self.play(Write(step2))
        
        # Fade old arrow
        self.play(arrows[0].animate.set_opacity(0.3))
        
        new_arrow2 = Arrow(
            start=nodes[0].get_bottom() + DOWN * 0.1,
            end=new_node.get_left() + LEFT * 0.1,
            color=RED,
            buff=0.1
        )
        self.play(GrowArrow(new_arrow2))
        self.wait(1)
        
        # Move new node into position
        self.play(FadeOut(step2))
        self.play(
            new_node.animate.move_to(nodes[0].get_center() + RIGHT * 1.75 + UP * 0.5),
            new_arrow1.animate.become(Arrow(
                start=nodes[0].get_center() + RIGHT * 2.85,
                end=nodes[1].get_left() + LEFT * 0.1,
                color=GREEN,
                buff=0.1
            )),
            new_arrow2.animate.become(Arrow(
                start=nodes[0].get_right() + RIGHT * 0.1,
                end=nodes[0].get_center() + RIGHT * 0.65,
                color=GREEN,
                buff=0.1
            ))
        )
        
        new_node.set_color(WHITE)
        self.wait(1)
        
        # Show time complexity
        self.play(FadeOut(operation))
        complexity = Text("Time Complexity: O(1)", font_size=32, color=GREEN)
        complexity.to_edge(DOWN, buff=1)
        self.play(Write(complexity))
        self.wait(2)
    
    def _create_node(self, value):
        box = Rectangle(height=1, width=2, color=WHITE, fill_opacity=0.2)
        value_text = Text(str(value), font_size=32, color=YELLOW)
        value_text.move_to(box.get_center() + LEFT * 0.4)
        pointer_box = Rectangle(height=1, width=0.6, color=GREEN, fill_opacity=0.1)
        pointer_box.next_to(box, RIGHT, buff=0)
        pointer_box.align_to(box, UP)
        return VGroup(box, value_text, pointer_box)


class LinkedListTraversal(Scene):
    """
    Show traversal through linked list.
    """
    
    def construct(self):
        title = Text("Linked List: Traversal", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Create list
        nodes = []
        arrows = []
        values = [10, 20, 30, 40]
        
        for i, val in enumerate(values):
            node = self._create_node(val)
            node.move_to(LEFT * 5 + RIGHT * i * 3 + UP * 0.5)
            nodes.append(node)
            self.play(Create(node), run_time=0.3)
            
            if i > 0:
                arrow = Arrow(
                    start=nodes[i-1].get_right() + RIGHT * 0.1,
                    end=nodes[i].get_left() + LEFT * 0.1,
                    color=GREEN,
                    buff=0.1
                )
                arrows.append(arrow)
                self.play(GrowArrow(arrow), run_time=0.3)
        
        self.wait(1)
        
        # Show traversal
        current_label = Text("current", font_size=24, color=RED)
        current_arrow = Arrow(start=UP, end=DOWN, color=RED).scale(0.5)
        
        for i, node in enumerate(nodes):
            # Position pointer
            current_arrow.next_to(node, DOWN, buff=0.3)
            current_label.next_to(current_arrow, DOWN, buff=0.1)
            
            if i == 0:
                self.play(GrowArrow(current_arrow), Write(current_label))
            else:
                self.play(
                    current_arrow.animate.next_to(node, DOWN, buff=0.3),
                    current_label.animate.next_to(current_arrow, DOWN, buff=0.4)
                )
            
            # Highlight current node
            self.play(node.animate.set_color(RED))
            self.wait(0.5)
            self.play(node.animate.set_color(WHITE))
        
        # Show time complexity
        complexity = Text("Time Complexity: O(n)", font_size=32, color=YELLOW)
        complexity.to_edge(DOWN, buff=1)
        self.play(Write(complexity))
        self.wait(2)
    
    def _create_node(self, value):
        box = Rectangle(height=1, width=2, color=WHITE, fill_opacity=0.2)
        value_text = Text(str(value), font_size=32, color=YELLOW)
        value_text.move_to(box.get_center() + LEFT * 0.4)
        pointer_box = Rectangle(height=1, width=0.6, color=GREEN, fill_opacity=0.1)
        pointer_box.next_to(box, RIGHT, buff=0)
        pointer_box.align_to(box, UP)
        return VGroup(box, value_text, pointer_box)
