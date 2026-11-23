# Buscador de Vagas de TI (LinkedIn)

API que busca posts de vagas no LinkedIn via Google (SerpAPI) e usa o Gemini para filtrar as vagas de TI e extrair cargo, empresa, local, nível e salário.

## Como rodar
```bash
pip install -r requirements.txt
```
Crie um `.env`:
```
_SERPAPI_KEY=sua_chave
_GEMINI_API_KEY=sua_chave
```
```bash
uvicorn main:app --reload
```
Exemplos:
- `http://localhost:8000/search?cidade=Curitiba&area=Python&paginas=2`
- `http://localhost:8000/docs` (documentação interativa)

Resultados ficam em cache por 1 hora (campo `cache` na resposta).

## Testes
```bash
pytest
```
Os testes usam mocks: não gastam cota do SerpAPI nem do Gemini.

## Limitações
Os dados vêm só do snippet do Google, então salário e nível frequentemente ficam nulos.
