#!/usr/bin/env python3
"""
CLI para análise de projetos remotos
"""
from core.project_analyzer import ProjectAnalyzer
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Analisa projetos remotos via P2P",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Análise rápida
  python3 scripts/analyze_project.py --host 100.73.184.97 --depth quick

  # Análise completa com relatório
  python3 scripts/analyze_project.py --host 100.73.184.97 --depth deep --output reports/mita.md
        """
    )

    parser.add_argument("--host", required=True, help="IP do peer")
    parser.add_argument("--port", type=int, default=9000,
                        help="Porta P2P (default: 9000)")
    parser.add_argument(
        "--depth",
        choices=["quick", "health", "deep"],
        default="quick",
        help="Profundidade da análise"
    )
    parser.add_argument("--output", help="Arquivo .md para salvar relatório")

    args = parser.parse_args()

    print(f"🔬 Analisando projeto em {args.host}:{args.port}")
    print(f"   Profundidade: {args.depth}")
    print()

    analyzer = ProjectAnalyzer(peer_host=args.host, peer_port=args.port)

    try:
        result = analyzer.analyze(depth=args.depth)

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        # Mostrar resumo no terminal
        print("\n" + "=" * 60)
        print("📊 RESUMO DA ANÁLISE")
        print("=" * 60)

        analysis = result.get('analysis', {})

        if 'tech_stack' in analysis:
            print("\n🛠️  Tech Stack:")
            for tech in analysis['tech_stack']:
                print(f"   • {tech}")

        if 'recommendations' in analysis:
            print("\n💡 Top Recomendações:")
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                print(f"   {i}. {rec}")

        # Gerar relatório se solicitado
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            analyzer.generate_report(result, str(output_path))
            print(f"\n📄 Relatório completo: {output_path}")

        print("\n✅ Análise concluída!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Análise cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
