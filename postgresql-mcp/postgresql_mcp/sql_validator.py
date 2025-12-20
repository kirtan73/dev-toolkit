"""
SQL validation and security module.
Ensures only read-only operations are allowed and prevents SQL injection.
"""

import re
from typing import Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class SQLValidator:
    """Validates SQL queries to ensure read-only operations only."""
    
    # SQL keywords that should be blocked (write operations)
    BLOCKED_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL'
    }
    
    # Allowed keywords for read operations
    ALLOWED_KEYWORDS = {
        'SELECT', 'WITH', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT',
        'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 'ORDER',
        'LIMIT', 'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT', 'AS',
        'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND',
        'OR', 'NOT', 'IN', 'EXISTS', 'LIKE', 'ILIKE', 'IS', 'NULL',
        'BETWEEN', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CAST',
        'COALESCE', 'NULLIF', 'EXTRACT', 'DATE_TRUNC'
    }
    
    @classmethod
    def validate_read_only(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the SQL query is read-only.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Empty query"
        
        # Normalize query: remove comments and extra whitespace
        normalized = cls._normalize_query(query)
        
        # Check for blocked keywords (case-insensitive)
        normalized_upper = normalized.upper()
        for keyword in cls.BLOCKED_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized_upper):
                logger.warning(
                    "Blocked keyword detected",
                    keyword=keyword,
                    query_preview=query[:100]
                )
                return False, f"Operation not allowed: {keyword} is not permitted for read-only access"
        
        # Basic structure validation - should start with SELECT or WITH
        normalized_trimmed = normalized.strip().upper()
        if not (normalized_trimmed.startswith('SELECT') or normalized_trimmed.startswith('WITH')):
            return False, "Query must be a SELECT statement or use WITH clause"
        
        # Check for potential SQL injection patterns
        if cls._detect_sql_injection(query):
            logger.warning("Potential SQL injection detected", query_preview=query[:100])
            return False, "Query contains potentially dangerous patterns"
        
        return True, None
    
    @classmethod
    def _normalize_query(cls, query: str) -> str:
        """Normalize SQL query by removing comments and extra whitespace."""
        # Remove single-line comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query.strip()
    
    @classmethod
    def _detect_sql_injection(cls, query: str) -> bool:
        """Detect common SQL injection patterns."""
        dangerous_patterns = [
            r';\s*(DROP|DELETE|INSERT|UPDATE)',  # Multiple statements
            r'UNION\s+SELECT',  # UNION injection (though UNION is allowed for valid queries)
            r'EXEC\s*\(',  # Executable code
            r'xp_cmdshell',  # SQL Server command execution
            r'LOAD_FILE',  # MySQL file loading
            r'INTO\s+OUTFILE',  # MySQL file writing
        ]
        
        normalized = cls._normalize_query(query).upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """
        Sanitize query by removing comments and normalizing whitespace.
        Note: This does not prevent SQL injection - use parameterized queries instead.
        """
        return cls._normalize_query(query)

