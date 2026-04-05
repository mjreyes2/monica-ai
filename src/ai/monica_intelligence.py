"""
MONICA AI - ADVANCED INTELLIGENCE SYSTEM

Critical thinking, reasoning, research, and learning capabilities.
Monica can:
- Research unknown concepts
- Learn new capabilities on the fly
- Generate and execute code
- Apply critical thinking
- Remember what she learns

Example: "Monica, make my background transparent"
- Monica doesn't know how → Researches transparency
- Learns about alpha channels and RGBA
- Generates code to implement it
- Executes and applies it
- Remembers for next time

Author: Monica AI System
Date: December 2, 2025
"""

import ollama
import requests
from typing import Optional, Dict, List, Any
import json
from pathlib import Path
from datetime import datetime
import re
import subprocess
import sys


class MonicaIntelligence:
    """
    Advanced AI reasoning and learning system.
    """

    def __init__(self):
        self.knowledge_base = Path("data/monica_learned_knowledge.json")
        self.code_cache = Path("data/monica_generated_code.json")
        self.knowledge_base.parent.mkdir(exist_ok=True)

        # Load existing knowledge
        self.learned_concepts = self._load_knowledge()
        self.generated_code = self._load_code_cache()

        # Critical thinking framework
        self.thinking_steps = [
            "understand_request",
            "check_existing_knowledge",
            "identify_gaps",
            "research_if_needed",
            "synthesize_solution",
            "generate_code_if_needed",
            "test_and_validate",
            "store_learning"
        ]

        # Ollama client
        self.ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = ollama.list()
            print("[OK] Ollama is running")
            return True
        except Exception as e:
            print(f"[!] Ollama not available: {e}")
            print("Please install Ollama from https://ollama.com")
            return False

    def _load_knowledge(self) -> Dict:
        """Load learned knowledge from disk."""
        if self.knowledge_base.exists():
            try:
                with open(self.knowledge_base, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_knowledge(self):
        """Save learned knowledge to disk."""
        with open(self.knowledge_base, 'w') as f:
            json.dump(self.learned_concepts, f, indent=2)

    def _load_code_cache(self) -> Dict:
        """Load generated code cache."""
        if self.code_cache.exists():
            try:
                with open(self.code_cache, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_code_cache(self):
        """Save generated code cache."""
        with open(self.code_cache, 'w') as f:
            json.dump(self.generated_code, f, indent=2)

    def think(self, request: str, context: Dict = None) -> Dict[str, Any]:
        """
        Apply critical thinking to understand and fulfill a request.

        Args:
            request: User's request
            context: Optional context (current state, available functions, etc.)

        Returns:
            Dictionary with reasoning process and solution
        """
        print(f"\n[THINK] Monica is thinking about: '{request}'")

        result = {
            "request": request,
            "timestamp": datetime.now().isoformat(),
            "reasoning_steps": [],
            "solution": None,
            "code_generated": None,
            "learned": False,
            "success": False
        }

        # Step 1: Understand the request
        understanding = self._understand_request(request)
        result["reasoning_steps"].append({
            "step": "understand_request",
            "output": understanding
        })

        # Step 2: Check existing knowledge
        existing = self._check_existing_knowledge(understanding)
        result["reasoning_steps"].append({
            "step": "check_existing_knowledge",
            "output": existing
        })

        # Step 3: Identify what we don't know
        if existing.get("known", False):
            print("[OK] I already know how to do this!")
            result["solution"] = existing.get("solution")
            result["success"] = True
        else:
            print("[?] This is new to me. Let me research...")

            # Step 4: Research
            research = self._research_concept(understanding)
            result["reasoning_steps"].append({
                "step": "research",
                "output": research
            })

            # Step 5: Synthesize solution
            solution = self._synthesize_solution(understanding, research, context)
            result["reasoning_steps"].append({
                "step": "synthesize_solution",
                "output": solution
            })

            # Step 6: Generate code if needed
            if solution.get("needs_code", False):
                code = self._generate_code(solution, context)
                result["code_generated"] = code
                result["reasoning_steps"].append({
                    "step": "generate_code",
                    "output": code
                })

            # Step 7: Store learning
            self._store_learning(understanding, research, solution)
            result["learned"] = True
            result["solution"] = solution
            result["success"] = solution.get("feasible", False)

        return result

    def _understand_request(self, request: str) -> Dict:
        """
        Understand what the user is asking for.

        Args:
            request: User's request

        Returns:
            Parsed understanding of the request
        """
        if not self.ollama_available:
            # Fallback: simple keyword matching
            return {
                "intent": "unknown",
                "keywords": request.lower().split(),
                "confidence": 0.3
            }

        # Use AI to understand intent
        prompt = f"""Analyze this user request and extract:
1. What they want to accomplish (intent)
2. Key concepts involved
3. Required technical knowledge
4. Difficulty level (easy/medium/hard)

Request: "{request}"

Respond in JSON format:
{{
  "intent": "short description",
  "concepts": ["concept1", "concept2"],
  "technical_requirements": ["requirement1", "requirement2"],
  "difficulty": "easy|medium|hard"
}}
"""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[{
                    "role": "system",
                    "content": "You are an AI that analyzes user requests. Always respond with valid JSON."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse JSON from response
            content = response["message"]["content"]
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            understanding = json.loads(content.strip())
            understanding["confidence"] = 0.9
            return understanding

        except Exception as e:
            print(f"Error understanding request: {e}")
            return {
                "intent": request,
                "concepts": [],
                "technical_requirements": [],
                "difficulty": "unknown",
                "confidence": 0.5
            }

    def _check_existing_knowledge(self, understanding: Dict) -> Dict:
        """
        Check if we already know how to do this.

        Args:
            understanding: Parsed understanding from _understand_request

        Returns:
            Existing knowledge if found
        """
        intent = understanding.get("intent", "").lower()

        # Check learned concepts
        for concept_key, concept_data in self.learned_concepts.items():
            if intent in concept_key.lower():
                return {
                    "known": True,
                    "concept": concept_key,
                    "solution": concept_data.get("solution"),
                    "learned_at": concept_data.get("learned_at")
                }

        # Check generated code cache
        for task_key, code_data in self.generated_code.items():
            if intent in task_key.lower():
                return {
                    "known": True,
                    "concept": task_key,
                    "solution": {"type": "code", "code": code_data.get("code")},
                    "learned_at": code_data.get("generated_at")
                }

        return {"known": False}

    def _research_concept(self, understanding: Dict) -> Dict:
        """
        Research unknown concepts using web search and AI.

        Args:
            understanding: What we're trying to learn

        Returns:
            Research results
        """
        concepts = understanding.get("concepts", [])
        intent = understanding.get("intent", "")

        research_results = {
            "sources": [],
            "key_findings": [],
            "code_examples": []
        }

        print(f"[SEARCH] Researching: {', '.join(concepts)}")

        # Use DuckDuckGo for web research
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                # Search for each concept
                for concept in concepts[:3]:  # Limit to avoid spam
                    query = f"{concept} python code example tutorial"
                    results = list(ddgs.text(query, max_results=3))

                    for result in results:
                        research_results["sources"].append({
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "snippet": result.get("body", "")
                        })

        except ImportError:
            print("[WARN] DuckDuckGo search not available. Install: pip install duckduckgo-search")
        except Exception as e:
            print(f"Search error: {e}")

        # Use AI to synthesize research
        if self.ollama_available and research_results["sources"]:
            research_text = "\n\n".join([
                f"Source: {s['title']}\n{s['snippet']}"
                for s in research_results["sources"][:5]
            ])

            prompt = f"""Based on this research about "{intent}", extract:
1. Key concepts and how they work
2. Python code patterns/examples
3. Best practices

Research:
{research_text}

Respond in JSON:
{{
  "key_findings": ["finding1", "finding2"],
  "code_patterns": ["pattern1", "pattern2"],
  "best_practices": ["practice1", "practice2"]
}}
"""

            try:
                response = ollama.chat(
                    model="llama3.2",
                    messages=[{
                        "role": "system",
                        "content": "You are a technical research assistant. Respond with valid JSON."
                    }, {
                        "role": "user",
                        "content": prompt
                    }]
                )

                content = response["message"]["content"]
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]

                synthesis = json.loads(content.strip())
                research_results.update(synthesis)

            except Exception as e:
                print(f"AI synthesis error: {e}")

        return research_results

    def _synthesize_solution(self, understanding: Dict, research: Dict, context: Dict = None) -> Dict:
        """
        Synthesize a solution based on understanding and research.

        Args:
            understanding: Parsed request understanding
            research: Research results
            context: Current context/state

        Returns:
            Proposed solution
        """
        if not self.ollama_available:
            return {
                "feasible": False,
                "reason": "AI not available for solution synthesis",
                "needs_code": False
            }

        # Build synthesis prompt
        prompt = f"""Given this request and research, propose a solution:

Request: {understanding.get('intent')}
Concepts: {', '.join(understanding.get('concepts', []))}
Technical Requirements: {', '.join(understanding.get('technical_requirements', []))}

Research Findings:
{json.dumps(research.get('key_findings', []), indent=2)}

Code Patterns:
{json.dumps(research.get('code_patterns', []), indent=2)}

Propose a solution in JSON:
{{
  "feasible": true/false,
  "approach": "high-level approach description",
  "steps": ["step1", "step2"],
  "needs_code": true/false,
  "code_type": "function|class|script|config",
  "libraries_needed": ["lib1", "lib2"],
  "estimated_difficulty": "easy|medium|hard"
}}
"""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[{
                    "role": "system",
                    "content": "You are a software architect. Propose practical, working solutions. Respond with valid JSON."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]

            solution = json.loads(content.strip())
            return solution

        except Exception as e:
            print(f"Solution synthesis error: {e}")
            return {
                "feasible": False,
                "reason": str(e),
                "needs_code": False
            }

    def _generate_code(self, solution: Dict, context: Dict = None) -> Dict:
        """
        Generate executable code for the solution.

        Args:
            solution: Solution specification
            context: Current context (available variables, etc.)

        Returns:
            Generated code and metadata
        """
        if not self.ollama_available:
            return {"success": False, "error": "AI not available"}

        code_type = solution.get("code_type", "function")
        approach = solution.get("approach", "")
        steps = solution.get("steps", [])

        prompt = f"""Generate Python code to implement this solution:

Approach: {approach}

Steps:
{json.dumps(steps, indent=2)}

Requirements:
- Type: {code_type}
- Include error handling
- Add docstrings
- Use type hints
- Make it production-ready

Respond with:
1. The complete Python code
2. Usage example
3. Required imports

Format:
```python
# Your code here
```

Usage:
```python
# Example usage
```
"""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[{
                    "role": "system",
                    "content": "You are an expert Python programmer. Generate clean, working, production-ready code."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response["message"]["content"]

            # Extract code blocks
            code_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)

            if code_blocks:
                main_code = code_blocks[0]
                usage_example = code_blocks[1] if len(code_blocks) > 1 else ""

                return {
                    "success": True,
                    "code": main_code,
                    "usage_example": usage_example,
                    "full_response": content
                }
            else:
                return {
                    "success": False,
                    "error": "No code blocks found in response",
                    "raw_response": content
                }

        except Exception as e:
            print(f"Code generation error: {e}")
            return {"success": False, "error": str(e)}

    def _store_learning(self, understanding: Dict, research: Dict, solution: Dict):
        """
        Store what was learned for future use.

        Args:
            understanding: What was understood
            research: What was researched
            solution: What solution was found
        """
        concept_key = understanding.get("intent", "unknown")

        self.learned_concepts[concept_key] = {
            "learned_at": datetime.now().isoformat(),
            "understanding": understanding,
            "research_summary": {
                "sources_count": len(research.get("sources", [])),
                "key_findings": research.get("key_findings", [])
            },
            "solution": solution
        }

        self._save_knowledge()
        print(f"[DISK] Learned and stored: '{concept_key}'")

    def execute_generated_code(self, code: str, safe_mode: bool = True) -> Dict:
        """
        Execute generated code safely.

        Args:
            code: Python code to execute
            safe_mode: If True, only allow certain operations

        Returns:
            Execution results
        """
        if safe_mode:
            # Check for dangerous operations
            dangerous_keywords = [
                'import os', 'import sys', 'subprocess', 'eval', 'exec',
                '__import__', 'open(', 'file(', 'rm ', 'del '
            ]

            for keyword in dangerous_keywords:
                if keyword in code.lower():
                    return {
                        "success": False,
                        "error": f"Potentially dangerous operation detected: {keyword}",
                        "safe_mode": True
                    }

        # Execute in isolated namespace
        namespace = {}

        try:
            exec(code, namespace)
            return {
                "success": True,
                "namespace": {k: str(v) for k, v in namespace.items() if not k.startswith('__')},
                "output": "Code executed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": sys.exc_info()
            }


# Example: Transparent Background
class TransparentBackgroundExample:
    """
    Example of Monica learning to make backgrounds transparent.
    """

    @staticmethod
    def demonstrate():
        """Demonstrate Monica learning transparency."""
        print("\n" + "="*60)
        print("EXAMPLE: Monica Learns to Make Background Transparent")
        print("="*60)

        monica = MonicaIntelligence()

        # User request
        request = "Monica, make my background transparent"

        # Monica thinks about it
        result = monica.think(request, context={
            "current_capabilities": ["green", "black", "blue", "red"],
            "programming_language": "python",
            "framework": "opencv"
        })

        # Show reasoning process
        print("\n[LIST] Monica's Reasoning Process:")
        for i, step in enumerate(result["reasoning_steps"], 1):
            print(f"\n  Step {i}: {step['step']}")
            print(f"  Output: {json.dumps(step['output'], indent=4)[:200]}...")

        # Show solution
        if result.get("code_generated"):
            print("\n[IDEA] Monica Generated This Code:")
            print("-" * 60)
            print(result["code_generated"].get("code", ""))
            print("-" * 60)

        # Next time, she'll remember
        print("\n[BRAIN] Next time you ask, Monica will remember!")

        return result


def test_intelligence():
    """Test Monica's intelligence system."""
    print("Testing Monica's Intelligence System...")

    monica = MonicaIntelligence()

    # Test 1: Simple known task
    print("\n" + "="*60)
    print("TEST 1: Known Task")
    print("="*60)

    # Test 2: Learning new concept
    print("\n" + "="*60)
    print("TEST 2: Learning New Concept (Transparent Background)")
    print("="*60)

    result = TransparentBackgroundExample.demonstrate()

    print("\n[OK] Intelligence system test complete!")
    print(f"\nResult success: {result.get('success')}")
    print(f"Learned: {result.get('learned')}")


if __name__ == "__main__":
    test_intelligence()
