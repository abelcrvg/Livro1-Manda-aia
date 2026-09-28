# Geração do e-book

Esta pasta contém a infraestrutura de teste para transformar o manuscrito em EPUB.

## Teste local

```bash
python -m pip install -r ebook/requirements.txt
python ebook/build_epub.py
```

O arquivo será criado em `dist/mandaçaia-melipona-quadrifasciata.epub`.

## GitHub Actions

O workflow `Build EPUB` pode ser executado manualmente pelo GitHub Actions. Ele reúne os arquivos Markdown da pasta `manuscrito/`, cria um sumário navegável, preserva links internos das referências e publica o EPUB como artefato da execução.

O objetivo desta primeira versão é testar a cadeia editorial. Depois podemos acrescentar capa, imagens, mapas, metadados completos, índice remissivo, validação EPUB e uma etapa específica de revisão para KDP.
