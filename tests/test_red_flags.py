import pytest
from dataclasses import asdict
from academic_investigator.core.red_flags import (
    RedFlagQuery,
    generate_person_red_flag_queries,
    generate_org_red_flag_queries,
    generate_lab_red_flag_queries,
    PERSON_RED_FLAG_TEMPLATES,
    ORG_RED_FLAG_TEMPLATES,
    LAB_RED_FLAG_TEMPLATES,
)


class TestRedFlagQuery:
    def test_red_flag_query_dataclass(self):
        query = RedFlagQuery(
            category="education",
            query="John Smith MIT retraction",
            severity="high",
            description="Retraction history at institution"
        )
        assert query.category == "education"
        assert query.query == "John Smith MIT retraction"
        assert query.severity == "high"
        assert query.description == "Retraction history at institution"

    def test_red_flag_query_to_dict(self):
        query = RedFlagQuery(
            category="education",
            query="John Smith MIT retraction",
            severity="high",
            description="Retraction history"
        )
        data = asdict(query)
        assert data == {
            "category": "education",
            "query": "John Smith MIT retraction",
            "severity": "high",
            "description": "Retraction history"
        }


class TestPersonRedFlagQueries:
    def test_generate_person_queries_basic(self):
        queries = generate_person_red_flag_queries("John Smith")
        assert len(queries) >= 10
        assert all(isinstance(q, RedFlagQuery) for q in queries)

    def test_generate_person_queries_with_affiliation(self):
        queries = generate_person_red_flag_queries("John Smith", "MIT")
        assert len(queries) >= 10
        # Check that MIT appears in queries where affiliation is used
        affiliation_queries = [q for q in queries if "{affiliation}" in
                               next(t[1] for t in PERSON_RED_FLAG_TEMPLATES if t[0] == q.category and t[2] == q.severity)]
        # At least some queries should contain MIT
        mit_queries = [q for q in queries if "MIT" in q.query]
        assert len(mit_queries) > 0

    def test_person_queries_no_unresolved_placeholders(self):
        queries = generate_person_red_flag_queries("John Smith", "MIT")
        for q in queries:
            assert "{name}" not in q.query
            assert "{affiliation}" not in q.query
            assert "{" not in q.query or "}" not in q.query

    def test_person_queries_without_affiliation(self):
        queries = generate_person_red_flag_queries("Jane Doe")
        for q in queries:
            assert "{name}" not in q.query
            assert "{affiliation}" not in q.query
            # Should handle missing affiliation gracefully
            assert "  " not in q.query  # No double spaces

    def test_person_queries_have_valid_severity(self):
        queries = generate_person_red_flag_queries("John Smith", "MIT")
        for q in queries:
            assert q.severity in ["high", "medium"]

    def test_person_queries_have_all_required_fields(self):
        queries = generate_person_red_flag_queries("John Smith")
        for q in queries:
            assert q.category
            assert q.query
            assert q.severity
            assert q.description


class TestOrgRedFlagQueries:
    def test_generate_org_queries_basic(self):
        queries = generate_org_red_flag_queries("BioNexus")
        assert len(queries) >= 9
        assert all(isinstance(q, RedFlagQuery) for q in queries)

    def test_generate_org_queries_with_founder(self):
        queries = generate_org_red_flag_queries("BioNexus", "John Doe")
        assert len(queries) >= 9
        # Check that founder name is used
        founder_queries = [q for q in queries if "John Doe" in q.query]
        assert len(founder_queries) > 0

    def test_org_queries_no_unresolved_placeholders(self):
        queries = generate_org_red_flag_queries("BioNexus", "John Doe")
        for q in queries:
            assert "{org_name}" not in q.query
            assert "{founder_name}" not in q.query
            assert "{" not in q.query or "}" not in q.query

    def test_org_queries_without_founder(self):
        queries = generate_org_red_flag_queries("TechCorp")
        for q in queries:
            assert "{org_name}" not in q.query
            assert "{founder_name}" not in q.query
            # Should use org_name as default for founder_name
            assert "  " not in q.query

    def test_org_queries_have_valid_severity(self):
        queries = generate_org_red_flag_queries("BioNexus")
        for q in queries:
            assert q.severity in ["high", "medium"]

    def test_org_queries_have_all_required_fields(self):
        queries = generate_org_red_flag_queries("BioNexus")
        for q in queries:
            assert q.category
            assert q.query
            assert q.severity
            assert q.description


class TestLabRedFlagQueries:
    def test_generate_lab_queries_with_lab_name(self):
        queries = generate_lab_red_flag_queries("John Smith", "Smith Lab")
        assert len(queries) >= 5
        assert all(isinstance(q, RedFlagQuery) for q in queries)

    def test_generate_lab_queries_default_lab_name(self):
        queries = generate_lab_red_flag_queries("Jane Doe")
        assert len(queries) >= 5
        # Should use default lab name format
        lab_queries = [q for q in queries if "lab" in q.query.lower()]
        assert len(lab_queries) > 0

    def test_lab_queries_no_unresolved_placeholders(self):
        queries = generate_lab_red_flag_queries("John Smith", "Smith Lab")
        for q in queries:
            assert "{pi_name}" not in q.query
            assert "{lab_name}" not in q.query
            assert "{" not in q.query or "}" not in q.query

    def test_lab_queries_have_valid_severity(self):
        queries = generate_lab_red_flag_queries("John Smith")
        for q in queries:
            assert q.severity in ["high", "medium"]

    def test_lab_queries_have_all_required_fields(self):
        queries = generate_lab_red_flag_queries("John Smith")
        for q in queries:
            assert q.category
            assert q.query
            assert q.severity
            assert q.description


class TestTemplateCategories:
    def test_person_template_categories_valid(self):
        valid_categories = {
            "education", "publication", "ethics", "career", "financial",
            "legal", "reputation", "alumni", "dropout", "graduation",
            "absence", "transparency"
        }
        for cat, _, _, _ in PERSON_RED_FLAG_TEMPLATES:
            assert cat in valid_categories, f"Invalid category: {cat}"

    def test_org_template_categories_valid(self):
        valid_categories = {
            "education", "publication", "ethics", "career", "financial",
            "legal", "reputation", "alumni", "dropout", "graduation",
            "absence", "transparency"
        }
        for cat, _, _, _ in ORG_RED_FLAG_TEMPLATES:
            assert cat in valid_categories, f"Invalid category: {cat}"

    def test_lab_template_categories_valid(self):
        valid_categories = {
            "education", "publication", "ethics", "career", "financial",
            "legal", "reputation", "alumni", "dropout", "graduation",
            "absence", "transparency"
        }
        for cat, _, _, _ in LAB_RED_FLAG_TEMPLATES:
            assert cat in valid_categories, f"Invalid category: {cat}"


class TestQueryFormatting:
    def test_person_query_clean_spacing(self):
        queries = generate_person_red_flag_queries("John Smith")
        for q in queries:
            # No leading/trailing spaces
            assert q.query == q.query.strip()
            # No double spaces
            assert "  " not in q.query

    def test_org_query_clean_spacing(self):
        queries = generate_org_red_flag_queries("BioNexus")
        for q in queries:
            assert q.query == q.query.strip()
            assert "  " not in q.query

    def test_lab_query_clean_spacing(self):
        queries = generate_lab_red_flag_queries("John Smith")
        for q in queries:
            assert q.query == q.query.strip()
            assert "  " not in q.query
