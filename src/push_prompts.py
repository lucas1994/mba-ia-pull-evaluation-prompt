"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def escape_unexpected_template_variables(text: str, allowed_variables: set[str]) -> str:
    def replace(match):
        variable = match.group(1)
        if variable in allowed_variables:
            return match.group(0)
        return "{{" + variable + "}}"

    return re.sub(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})", replace, text)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        allowed_variables = {"bug_report"}
        system_prompt = escape_unexpected_template_variables(
            prompt_data["system_prompt"].strip(),
            allowed_variables,
        )
        user_prompt = escape_unexpected_template_variables(
            prompt_data.get("user_prompt", "{bug_report}").strip(),
            allowed_variables,
        )

        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        prompt_template = ChatPromptTemplate.from_messages(messages)

        tags = list(prompt_data.get("tags", []))
        version = prompt_data.get("version")
        if version and version not in tags:
            tags.append(version)

        for technique in prompt_data.get("techniques_applied", []):
            technique_tag = f"technique:{technique}"
            if technique_tag not in tags:
                tags.append(technique_tag)

        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt_template,
            description=prompt_data.get("description", f"Prompt {prompt_name}"),
            tags=tags,
        )

        print(f"   ✓ Prompt publicado com sucesso: {url}")
        return True
    except Exception as e:
        if "Nothing to commit" in str(e):
            print("   ✓ Nenhuma alteração para publicar (prompt já está atualizado)")
            return True

        print(f"   ❌ Erro ao publicar prompt '{prompt_name}': {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    for field in ["description", "system_prompt", "user_prompt", "version"]:
        value = prompt_data.get(field, "")
        if isinstance(value, str) and not value.strip():
            errors.append(f"Campo obrigatório vazio: {field}")

    for field in ["system_prompt", "user_prompt"]:
        content = prompt_data.get(field, "")
        if "[TODO]" in content or "TODO" in content:
            errors.append(f"{field} ainda contém TODOs")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append("O prompt deve listar pelo menos 2 técnicas em 'techniques_applied'")

    tags = prompt_data.get("tags", [])
    if tags and not isinstance(tags, list):
        errors.append("O campo 'tags' deve ser uma lista")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"
    if not prompt_file.exists():
        print(f"❌ Arquivo de prompt não encontrado: {prompt_file}")
        print("\nCrie o arquivo prompts/bug_to_user_story_v2.yml antes de executar o push.")
        return 1

    yaml_data = load_yaml(str(prompt_file))
    if not yaml_data:
        return 1

    if "description" in yaml_data and "system_prompt" in yaml_data:
        prompt_key = "bug_to_user_story_v2"
        prompt_data = yaml_data
    else:
        prompt_items = [(key, value) for key, value in yaml_data.items() if isinstance(value, dict)]
        if not prompt_items:
            print("❌ Estrutura YAML inválida. Nenhum prompt encontrado no arquivo.")
            return 1
        prompt_key, prompt_data = prompt_items[0]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido. Corrija os itens abaixo antes do push:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    prompt_name = f"{username}/{prompt_key}"

    print(f"Prompt local: {prompt_file.name}")
    print(f"Prompt remoto: {prompt_name}")
    print(f"Versão: {prompt_data.get('version', 'N/A')}")

    techniques = prompt_data.get("techniques_applied", [])
    if techniques:
        print(f"Técnicas: {', '.join(techniques)}")

    success = push_prompt_to_langsmith(prompt_name, prompt_data)
    if not success:
        return 1

    print("\nPróximos passos:")
    print("1. Verifique o prompt publicado no dashboard do LangSmith")
    print("2. Deixe o prompt público, se necessário")
    print("3. Execute a avaliação com: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
