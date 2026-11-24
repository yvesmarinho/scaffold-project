#!/usr/bin/env python3
"""
Teste completo do objetivo wizard com TODAS as variáveis preenchidas.
Use como POC para validar geração de objetivo.yaml.

Execução:
    pytest tests/test_objetivo_wizard_complete_poc.py -v -s

Gera arquivo de saída:
    /tmp/objetivo-poc-complete.yaml
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.objetivo_wizard import ObjetivoWizard, WizardAnswers


def test_complete_objective_all_variables(tmp_path):
    """
    POC: Teste com TODAS as 10 questões respondidas.
    Cobre todos os placeholders do template.
    """
    wizard = ObjetivoWizard()

    # Criar respostas completas para todas as 10 questões
    answers = WizardAnswers(
        project_name="sistema-deploy-automatizado",
        project_title="Sistema de Deploy Automatizado para Plataforma Cloud",
        project_type="new",  # "new" | "update"
        project_domain="devops",  # programming | infrastructure | security | data
        project_language="python",  # python | typescript | go | terraform
        created_by="Yves Marinho",
        answers={
            # Q1: O que este projeto faz? (P0 - obrigatório)
            "{{DESCRIPTION}}": (
                "Sistema automatizado de deploy que permite equipes DevOps configurar e "
                "executar deploys via interface web/CLI, com rollback automático em caso "
                "de falha e monitoramento integrado."
            ),
            # Q2: Qual problema está sendo melhorado? (P0 condicional - apenas para "update")
            # Deixar vazio ou comentar se project_type="new"
            # "{{ANSWER_2}}": (
            #     "Sistema atual: deploys manuais levam 2-3h com 15% de erro. "
            #     "Performance degrada em 50%, custos operacionais +R$ 30k/mês. "
            #     "Falta automação, padronização e observabilidade."
            # ),
            # Q3: O que está NO escopo? (P0 - obrigatório, multiline)
            "{{FEATURE}}": (
                "Processamento automático de deploy com validação de pré-requisitos (P0)\n"
                "Interface web para configuração e monitoramento de deploys (P1)\n"
                "API REST para integração com CI/CD pipelines (P0)\n"
                "Sistema de rollback automático baseado em health checks (P0)\n"
                "Notificações por email/Slack em eventos críticos (P2)\n"
                "Dashboard de métricas e histórico de deploys (P1)"
            ),
            # Q4: Restrições técnicas? (P1 - opcional, multiline)
            "{{CONSTRAINT}}": (
                "Budget: R$ 80k para desenvolvimento + R$ 5k/mês infraestrutura\n"
                "Prazo: 4 meses para MVP (3 sprints de 4 semanas)\n"
                "Compatibilidade obrigatória com LGPD e SOC2\n"
                "Performance: API deve responder em <200ms p95\n"
                "Disponibilidade: 99.9% SLA (máx 43min downtime/mês)\n"
                "Segurança: autenticação via OAuth2 + RBAC"
            ),
            # Q5: Regras de negócio complexas? (P1 - opcional, multiline)
            "{{RULE}}": (
                "Apenas usuários com role 'deployer' podem executar deploys em produção\n"
                "Deploys em produção requerem aprovação de 2 reviewers\n"
                "Janela de deploy em produção: seg-qui 9h-17h, sexta até 15h\n"
                "Rollback automático se >5% de health checks falharem em 2min\n"
                "Logs de deploy devem ser retidos por 2 anos (compliance)\n"
                "Rate limit: máximo 10 deploys simultâneos por cluster"
            ),
            # Q6: Tipo de solução técnica (P0 - obrigatório)
            "{{RESPONSE}}": (
                "código Python 3.11+ com FastAPI, PostgreSQL para persistência, "
                "Redis para cache/queue, Celery para tasks assíncronas, "
                "Docker/Kubernetes para deploy, padrão hexagonal/clean architecture"
            ),
            # Q7: Padrão de documentação (P1 - opcional)
            "{{DOCSTYLE}}": (
                "Google Style Docstrings com type hints completos, "
                "Sphinx para geração de docs, ADRs para decisões arquiteturais, "
                "OpenAPI/Swagger para documentação de API"
            ),
            # Q8: Infraestrutura necessária (P1 - opcional, multiline)
            "{{INFRASTRUCTURE}}": (
                "Cluster Kubernetes 1.28+ em AWS EKS (3 nodes t3.medium)\n"
                "Banco PostgreSQL 15 em RDS (db.t3.medium, 100GB storage)\n"
                "Redis 7.x em ElastiCache (cache.t3.micro)\n"
                "S3 bucket para artefatos de deploy e backups\n"
                "CloudWatch/Prometheus para monitoramento\n"
                "Application Load Balancer com WAF habilitado"
            ),
            # Q9: Perfis/roles necessários (P1 - opcional, multiline)
            "{{PROFILE_ROLE_1}}": (
                "backend-architect (Python/FastAPI expert, senior 5+ anos)\n"
                "devops-engineer (K8s/AWS expert, senior 3+ anos)\n"
                "database-expert (PostgreSQL performance tuning, pleno 2+ anos)\n"
                "qa-automation (pytest/integration tests, pleno)\n"
                "tech-writer (documentação técnica, júnior)"
            ),
            # Q10: Resultados esperados mensuráveis (P0 - obrigatório, multiline)
            "{{EXPECTED_OUTCOME}}": (
                "100% dos deploys via sistema automatizado (zero deploys manuais)\n"
                "Tempo médio de deploy reduzido de 2-3h para <15min\n"
                "Taxa de erro de deploy reduzida de 15% para <2%\n"
                "Rollback automático em <5min quando necessário\n"
                "Economia operacional de R$ 30k/mês em horas-homem\n"
                "Aumento de 50% na frequência de deploys (de 10/mês para 15/mês)\n"
                "SLA de 99.9% alcançado consistentemente\n"
                "Zero incidentes de segurança relacionados a deploys"
            ),
        },
    )

    # Executar wizard em modo não-interativo
    output_path = tmp_path / "objetivo-init.yaml"
    exit_code = wizard.run_non_interactive(answers, output_path=output_path)

    # Validar que execução foi bem-sucedida
    assert exit_code == 0, f"Wizard retornou erro: exit_code={exit_code}"

    # Validar que arquivo foi criado
    assert output_path.exists(), f"Arquivo {output_path} não foi criado"

    # Ler conteúdo gerado
    content = output_path.read_text()

    # Validar que não há placeholders não substituídos
    import re

    unreplaced = re.findall(r"\{\{[A-Z_0-9]+\}\}", content)
    assert not unreplaced, f"Placeholders não substituídos: {unreplaced}"

    # Validar que campos obrigatórios estão presentes (formato objetivo-init.yaml v2.0)
    assert 'version: "2.0"' in content
    assert 'name: "sistema-deploy-automatizado"' in content
    assert 'created_by: "Yves Marinho"' in content

    # Validar que respostas foram incluídas (apenas campos que existem no template)
    assert "Sistema automatizado de deploy" in content  # Q1 - DESCRIPTION
    assert "Processamento automático de deploy" in content  # Q3 - FEATURE_1
    assert "Apenas usuários com role 'deployer'" in content  # Q5 - RULE_1
    assert "Python 3.11+ com FastAPI" in content  # Q6 - RESPONSE
    assert "Google Style Docstrings" in content  # Q7 - DOCSTYLE
    assert "Cluster Kubernetes 1.28+" in content  # Q8 - INFRASTRUCTURE_1
    assert (
        "100% dos deploys via sistema automatizado" in content
    )  # Q10 - EXPECTED_OUTCOME_1

    # Nota: CONSTRAINT e PROFILE_ROLE não estão no template atual

    # Copiar para /tmp para inspeção manual
    poc_output = Path("/tmp/objetivo-poc-complete.yaml")
    poc_output.write_text(content)

    print(f"\n{'='*80}")
    print("✅ POC gerado com sucesso!")
    print(f"{'='*80}")
    print(f"📄 Arquivo gerado: {poc_output}")
    print(f"📊 Tamanho: {len(content)} bytes")
    print(f"📋 Linhas: {len(content.splitlines())}")
    print("\n🔍 Preview (primeiras 30 linhas):")
    print(f"{'='*80}")
    for i, line in enumerate(content.splitlines()[:30], 1):
        print(f"{i:3d} | {line}")
    print(f"{'='*80}")
    print("\n💡 Use este arquivo como base para:")
    print("   1. Validar template objetivo-init-template.yaml")
    print("   2. Criar objetivo.yaml para projetos reais")
    print("   3. Testar integração com SpecKit")
    print(f"{'='*80}\n")

    # Retorna o path para uso em pytest
    return 0  # Success


def test_minimal_objective_required_only(tmp_path):
    """
    POC: Teste com APENAS questões obrigatórias (P0).
    Valida comportamento mínimo do wizard.
    """
    wizard = ObjetivoWizard()

    answers = WizardAnswers(
        project_name="poc-minimal",
        project_title="POC Minimal - Apenas P0",
        project_type="new",
        project_domain="programming",
        project_language="python",
        created_by="POC Test",
        answers={
            # Apenas P0 obrigatórios
            "{{DESCRIPTION}}": "Sistema de exemplo minimalista para validação",
            "{{FEATURE}}": "Feature básica 1\nFeature básica 2",
            "{{RESPONSE}}": "código Python básico",
            "{{EXPECTED_OUTCOME}}": "Sistema funcional\nTestes passando",
        },
    )

    output_path = tmp_path / "objetivo-init-minimal.yaml"
    exit_code = wizard.run_non_interactive(answers, output_path=output_path)
    assert exit_code == 0, f"Wizard retornou erro: exit_code={exit_code}"
    assert output_path.exists()

    content = output_path.read_text()

    # Copiar para /tmp
    poc_minimal = Path("/tmp/objetivo-poc-minimal.yaml")
    poc_minimal.write_text(content)

    print(f"\n{'='*80}")
    print("✅ POC Minimal gerado!")
    print(f"📄 Arquivo: {poc_minimal}")
    print(f"{'='*80}\n")

    return 0  # Success


if __name__ == "__main__":
    """Execução standalone para gerar POCs rapidamente."""
    import sys
    import tempfile

    _standalone_dir = Path(tempfile.mkdtemp(prefix="objetivo-poc-"))

    print("\n🚀 Gerando POCs de objetivo.yaml...\n")

    # POC 1: Completo com todas as variáveis
    try:
        test_complete_objective_all_variables(_standalone_dir)
        print("✅ POC Completo gerado")
    except Exception as e:
        print(f"❌ Erro no POC Completo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # POC 2: Minimal apenas P0
    try:
        test_minimal_objective_required_only(_standalone_dir)
        print("✅ POC Minimal gerado")
    except Exception as e:
        print(f"❌ Erro no POC Minimal: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🎯 Sucesso! 2 POCs gerados:")
    print("   - /tmp/objetivo-poc-complete.yaml (TODAS as variáveis)")
    print("   - /tmp/objetivo-poc-minimal.yaml (apenas P0 obrigatórias)")
    print("=" * 80 + "\n")
