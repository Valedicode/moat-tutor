"""
Response parser for converting agent text responses to structured data.

The agent outputs responses following a 9-section structure as defined in the system prompt:
1. Summary
2. Key Events
3. Price Behavior
4. MOAT Analysis
5. Plain-Language Explanation
6. Concept Definitions
7. Learning Options
8. Comprehension Check
9. Next Steps
"""

import re
from typing import Dict, List, Optional, Tuple

from api.models.responses import ParsedAnalysis, MoatAnalysis, LearningOption


class AgentResponseParser:
    """
    Parses structured text responses from the MoatTutor agent.
    
    The parser is designed to be flexible and handle cases where the agent
    doesn't perfectly follow the format.
    """
    
    # Section headers to look for (case-insensitive)
    SECTION_PATTERNS = {
        "summary": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:1\.\s*)?(?:\*\*)?Summary(?:\*\*)?:?\s*(?:\*\*)?",
        "key_events": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:2\.\s*)?(?:\*\*)?Key Events(?:\*\*)?:?\s*(?:\*\*)?",
        "price_behavior": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:3\.\s*)?(?:\*\*)?Price Behavior(?:\*\*)?:?\s*(?:\*\*)?",
        "moat_analysis": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:4\.\s*)?(?:\*\*)?MOAT Analysis(?:\*\*)?:?\s*(?:\*\*)?",
        "plain_explanation": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:5\.\s*)?(?:\*\*)?Plain(?:-|\s)Language Explanation(?:\*\*)?:?\s*(?:\*\*)?",
        "concept_definitions": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:6\.\s*)?(?:\*\*)?Concept Definitions(?:\*\*)?:?\s*(?:\*\*)?",
        "learning_options": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:7\.\s*)?(?:\*\*)?Learning Options(?:\*\*)?:?\s*(?:\*\*)?",
        "comprehension_check": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:8\.\s*)?(?:\*\*)?Comprehension Check(?:\*\*)?:?\s*(?:\*\*)?",
        "next_steps": r"(?:^|\n)(?:##?\s*)?(?:\*\*)?(?:9\.\s*)?(?:\*\*)?Next Steps(?:\*\*)?:?\s*(?:\*\*)?",
    }
    
    @staticmethod
    def parse(response_text: str, ticker: Optional[str] = None, 
              start_date: Optional[str] = None, end_date: Optional[str] = None) -> ParsedAnalysis:
        """
        Parse agent response text into structured ParsedAnalysis.
        
        Args:
            response_text: The raw text response from the agent
            ticker: Optional ticker symbol (if known from request)
            start_date: Optional start date (if known from request)
            end_date: Optional end date (if known from request)
            
        Returns:
            ParsedAnalysis object with extracted data
        """
        parser = AgentResponseParser()
        
        # Split response into sections
        sections = parser._split_into_sections(response_text)
        
        # Extract metadata if not provided
        if not ticker:
            ticker = parser._extract_ticker(response_text)
        if not start_date or not end_date:
            extracted_start, extracted_end = parser._extract_dates(response_text)
            start_date = start_date or extracted_start
            end_date = end_date or extracted_end
        
        # Parse each section
        summary = parser._extract_summary(sections.get("summary", ""))
        key_events = parser._extract_key_events(sections.get("key_events", ""))
        price_behavior = parser._extract_price_behavior(sections.get("price_behavior", ""))
        moat_analysis = parser._parse_moat_analysis(sections.get("moat_analysis", ""))
        plain_explanation = parser._extract_plain_explanation(sections.get("plain_explanation", ""))
        concept_definitions = parser._parse_concept_definitions(sections.get("concept_definitions", ""))
        learning_options = parser._parse_learning_options(sections.get("learning_options", ""))
        comprehension_questions = parser._extract_comprehension_questions(sections.get("comprehension_check", ""))
        next_steps = parser._extract_next_steps(sections.get("next_steps", ""))
        
        return ParsedAnalysis(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            key_events=key_events,
            price_behavior=price_behavior,
            moat_analysis=moat_analysis,
            plain_explanation=plain_explanation,
            concept_definitions=concept_definitions,
            learning_options=learning_options,
            comprehension_questions=comprehension_questions,
            next_steps=next_steps,
            raw_response=response_text
        )
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split the response text into sections based on headers."""
        sections = {}
        
        # Find all section positions
        section_positions = []
        for section_name, pattern in self.SECTION_PATTERNS.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                section_positions.append((match.start(), section_name, match.end()))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[0])
        
        # Extract content between sections
        for i, (start_pos, section_name, header_end) in enumerate(section_positions):
            # Find where this section ends (start of next section or end of text)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract section content (skip the header)
            content = text[header_end:end_pos].strip()
            sections[section_name] = content
        
        return sections
    
    def _extract_ticker(self, text: str) -> Optional[str]:
        """Extract ticker symbol from text."""
        # Look for common ticker patterns
        patterns = [
            r'\b([A-Z]{1,5})\b(?:\s+stock|\s+moved|\s+from)',  # AAPL stock, AAPL moved
            r'ticker[:\s]+([A-Z]{1,5})\b',  # ticker: AAPL
            r'\$([A-Z]{1,5})\b',  # $AAPL
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_dates(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract start and end dates from text."""
        # Look for date range patterns
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 2:
            return dates[0], dates[1]
        elif len(dates) == 1:
            return dates[0], dates[0]
        
        return None, None
    
    def _extract_summary(self, content: str) -> Optional[str]:
        """Extract summary text."""
        if not content:
            return None
        # Take the first paragraph or up to first newline
        lines = content.split('\n')
        summary_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                summary_lines.append(line)
                # Stop after a few sentences (roughly 2-3)
                if len(summary_lines) >= 3:
                    break
        return ' '.join(summary_lines) if summary_lines else None
    
    def _extract_key_events(self, content: str) -> List[str]:
        """Extract key events as a list."""
        if not content:
            return []
        
        events = []
        # Look for bullet points or numbered lists
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullets (-, *, •) or numbers (1., 2.)
            match = re.match(r'^(?:[-*•]|\d+\.)\s+(.+)$', line)
            if match:
                events.append(match.group(1).strip())
            elif line and not line.startswith('#'):
                # If not a list item but has content, add it
                events.append(line)
        
        return events
    
    def _extract_price_behavior(self, content: str) -> Optional[str]:
        """Extract price behavior description."""
        if not content:
            return None
        # Return the full content, cleaning up extra whitespace
        return ' '.join(content.split())
    
    def _parse_moat_analysis(self, content: str) -> Optional[MoatAnalysis]:
        """Parse MOAT analysis section."""
        if not content:
            return None
        
        strengthened = []
        weakened = []
        relevant = []
        
        # Look for specific patterns
        content_lower = content.lower()
        
        # Extract strengthened moats
        strengthen_match = re.search(
            r'strengthen(?:ed)?[:\s]+([^\n]+)',
            content,
            re.IGNORECASE
        )
        if strengthen_match:
            strengthened = [s.strip() for s in strengthen_match.group(1).split(',')]
        
        # Extract weakened moats
        weaken_match = re.search(
            r'weaken(?:ed)?[:\s]+([^\n]+)',
            content,
            re.IGNORECASE
        )
        if weaken_match:
            weakened = [s.strip() for s in weaken_match.group(1).split(',')]
        
        # Extract relevant moats
        relevant_match = re.search(
            r'relevant[:\s]+([^\n]+)',
            content,
            re.IGNORECASE
        )
        if relevant_match:
            relevant = [s.strip() for s in relevant_match.group(1).split(',')]
        
        # If no specific patterns found, look for moat keywords in content
        moat_keywords = [
            "Network Effects",
            "Switching Costs",
            "Intangible Assets",
            "Cost Advantages",
            "Efficient Scale"
        ]
        
        if not (strengthened or weakened or relevant):
            for keyword in moat_keywords:
                if keyword.lower() in content_lower:
                    relevant.append(keyword)
        
        return MoatAnalysis(
            strengthened=strengthened,
            weakened=weakened,
            relevant=relevant,
            explanation=content.strip()
        )
    
    def _extract_plain_explanation(self, content: str) -> Optional[str]:
        """Extract plain language explanation."""
        if not content:
            return None
        return ' '.join(content.split())
    
    def _parse_concept_definitions(self, content: str) -> Dict[str, str]:
        """Parse concept definitions into a dictionary."""
        if not content:
            return {}
        
        definitions = {}
        
        # Look for "**Term**: Definition" pattern
        pattern = r'\*\*([^*]+)\*\*[:\s]+([^\n]+)'
        matches = re.findall(pattern, content)
        
        for term, definition in matches:
            definitions[term.strip()] = definition.strip()
        
        # Also try "Term: Definition" without bold
        if not definitions:
            lines = content.split('\n')
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        term = parts[0].strip('- *').strip()
                        definition = parts[1].strip()
                        if term and definition:
                            definitions[term] = definition
        
        return definitions
    
    def _parse_learning_options(self, content: str) -> List[LearningOption]:
        """Parse learning options."""
        if not content:
            return []
        
        options = []
        
        # Look for bullet points with descriptions
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Match "- **Label**: Description" pattern
            match = re.match(r'^[-*•]\s*\*\*([^*]+)\*\*[:\s]+(.+)$', line)
            if match:
                label = match.group(1).strip()
                description = match.group(2).strip()
                option_id = label.lower().replace(' ', '-').replace(':', '')
                options.append(LearningOption(
                    id=option_id,
                    label=label,
                    description=description
                ))
        
        return options
    
    def _extract_comprehension_questions(self, content: str) -> List[str]:
        """Extract comprehension check questions."""
        if not content:
            return []
        
        questions = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullets or questions ending with "?"
            if line.endswith('?'):
                # Remove bullet points
                question = re.sub(r'^[-*•]\s+', '', line)
                questions.append(question.strip())
        
        return questions
    
    def _extract_next_steps(self, content: str) -> List[str]:
        """Extract suggested next steps."""
        if not content:
            return []
        
        steps = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullets or quoted suggestions
            match = re.match(r'^(?:[-*•]|\d+\.)\s+["\']?(.+?)["\']?$', line)
            if match:
                steps.append(match.group(1).strip())
            elif line and not line.startswith('#'):
                # Add non-empty lines that aren't headers
                steps.append(line)
        
        return steps

