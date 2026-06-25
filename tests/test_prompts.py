"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    @pytest.fixture(scope="class")
    def prompt_data(self):
        prompts = load_prompts(str(PROMPT_FILE))
        assert "bug_to_user_story_v2" in prompts
        return prompts["bug_to_user_story_v2"]

    @pytest.fixture(scope="class")
    def system_prompt(self, prompt_data):
        return prompt_data.get("system_prompt", "")

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompts = load_prompts(str(PROMPT_FILE))
        prompt_data = prompts["bug_to_user_story_v2"]

        is_valid, errors = validate_prompt_structure(prompt_data)

        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip()
        assert "system_prompt está vazio" not in errors
        assert is_valid

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt_text = system_prompt.lower()

        assert "você especialista em histórias do agil" in prompt_text
        assert "transformar relatos de bugs de usuários em tarefas para desenvolvedores" in prompt_text

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_text = system_prompt.lower()

        assert "# templates de user story" in prompt_text
        assert "template - user story simples" in prompt_text
        assert "template - user story detalhada" in prompt_text
        assert "template - user story de segurança" in prompt_text
        assert "template - user story funcional" in prompt_text
        assert "#templates - complexo" in prompt_text
        assert "critérios de aceitação" in prompt_text

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_text = system_prompt.lower()

        assert "exemplo de uso" in prompt_text
        assert "exemplo de uso 2" in prompt_text
        assert "exemplo adicional" in prompt_text
        assert "user story gerada" in prompt_text
        assert "título:" in prompt_text
        assert "critérios de aceitação" in prompt_text or "criterios de aceitacao" in prompt_text
        assert prompt_text.count("user story gerada") >= 3

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_text = "\n".join(
            str(value)
            for value in prompt_data.values()
            if isinstance(value, (str, list))
        )

        assert "[TODO]" not in prompt_text
        assert "TODO" not in prompt_text

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        normalized_techniques = {technique.lower() for technique in techniques}

        assert isinstance(techniques, list)
        assert len(techniques) >= 2
        assert "few-shot-learning" in normalized_techniques
        assert "role-prompting" in normalized_techniques
        assert "chain-of-thought" in normalized_techniques
        assert "skeleton-templates" in normalized_techniques
        assert "least-to-most decomposition" in normalized_techniques

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
