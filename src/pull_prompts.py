"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def _extract_message_template(message) -> str:
    prompt = getattr(message, "prompt", None)
    if prompt is not None and hasattr(prompt, "template"):
        return prompt.template

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content

    return ""


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt remoto e salva em YAML local.

    Returns:
        True se sucesso, False caso contrário
    """
    prompt_identifier = "leonanluppi/bug_to_user_story_v1"
    output_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"

    try:
        print(f"Baixando prompt do LangSmith Hub: {prompt_identifier}")
        prompt = hub.pull(prompt_identifier)

        system_prompt = ""
        user_prompt = "{bug_report}"

        if hasattr(prompt, "messages") and prompt.messages:
            for message in prompt.messages:
                message_class = message.__class__.__name__.lower()
                content = _extract_message_template(message)

                if "system" in message_class and content and not system_prompt:
                    system_prompt = content
                elif ("human" in message_class or "user" in message_class) and content:
                    user_prompt = content
        elif hasattr(prompt, "template"):
            user_prompt = prompt.template

        print(f"✓ Prompt '{prompt_identifier}' baixado com sucesso.")

        if not system_prompt:
            raise ValueError("Não foi possível extrair o system prompt do objeto retornado pelo Hub.")

        prompt_data = {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "source_prompt": prompt_identifier,
                "tags": ["bug-analysis", "user-story", "product-management"],
            }
        }

        if not save_yaml(prompt_data, str(output_path)):
            return False

        print(f"✓ Prompt salvo localmente em: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{prompt_identifier}': {e}")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    if pull_prompts_from_langsmith():
        print("\nPróximos passos:")
        print("1. Revise o conteúdo de prompts/bug_to_user_story_v1.yml")
        print("2. Crie a versão otimizada em prompts/bug_to_user_story_v2.yml")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
