# AutoTesting pentru Testarea Sistemelor Software

## 1. Scopul aplicatiei

Aplicatia genereaza automat teste unitare `pytest` pentru functia aflata in `to_test.py`, folosind un model local Ollama. Testele generate sunt validate automat si sunt pastrate numai daca sunt valide si imbunatatesc performanta categoriei curente.

Performanta este calculata separat pentru fiecare categorie de teste:

- `pytest`: verifica daca suita de teste ruleaza corect;
- `coverage.py`: masoara statement coverage si branch coverage pentru `to_test.py`;
- `mutmut`: masoara cati mutanti sunt eliminati de teste.

Categoriile implicite sunt:

- `functional`: teste generate in `test_functional.py`, pe baza instructiunilor din `testing_functional.md`;
- `structural`: teste generate in `test_structural.py`, pe baza instructiunilor din `testing_structural.md`.

Optimizarea se face separat pe categorie. Daca o categorie ajunge la 100% pytest, 100% coverage si 100% mutanti eliminati, categoria respectiva se opreste independent de cealalta categorie.

## 2. Structura proiectului

```text
AutoTesting.py         # orchestratorul principal
config.py              # configurarea principala, in format Python apropiat de JSON
reset.py               # resetarea workspace-ului
manual_testing.py      # rulare manuala pytest / coverage / mutmut in root
run_examples.py        # pregatirea exemplelor din examples/
run_arh_manual.py      # rulare manuala pe folderele salvate in arh/
run_auto.sh            # script shell pentru rularea fluxului automat
run_manual.sh          # script shell pentru rularea manuala pe arhive
Rules.md               # reguli generale pentru generarea testelor
testing_functional.md  # instructiuni numerotate pentru teste functionale
testing_structural.md  # instructiuni numerotate pentru teste structurale
to_test.py             # functia curenta testata
test_functional.py     # teste functionale acceptate
test_structural.py     # teste structurale acceptate
test_propunere.py      # fisier temporar pentru candidatul curent
Includes/              # module interne ale framework-ului
examples/              # functii de exemplu pentru testarea framework-ului
arh/                   # arhive ale rularilor finalizate
logs/                  # loguri tehnice si dialoguri Ollama
```

`config.py` din root este fisierul recomandat pentru reglaje uzuale. `Includes/Config.py` este adaptor intern si nu trebuie sters, deoarece modulele din `Includes/` il folosesc pentru incarcarea setarilor.

## 3. Dependinte

Instalare utilitare principale:

```bash
python3 -m pip install --user --break-system-packages pytest coverage mutmut
```

Instalare Ollama si model local:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama -v
```

Verificari utile:

```bash
python3 -m pytest --version
python3 -m coverage --version
mutmut --version
ollama list
```

## 4. Configurare

Configurarea principala se afla in `config.py`. Fisierul este Python pentru a permite comentarii, dar structura este apropiata de JSON: o singura variabila `CONFIG`, impartita pe sectiuni.

Setari importante:

- `timeouts.timeout_sec`: timeout general pentru comenzi obisnuite si pentru apelul HTTP catre Ollama;
- `timeouts.timeout_sec_mutmut`: timeout separat pentru `mutmut`;
- `timeouts.timeout_categorie_ai_sec`: buget maxim de timp pentru etapa de descoperire dintr-o categorie;
- `timeouts.max_corectie_attempts`: cate corectii se cer pentru o propunere invalida;
- `timeouts.max_empty_answers_consecutive`: cate raspunsuri goale sau inutilizabile consecutive sunt acceptate inainte de renuntare;
- `generation_limits.max_existing_subtype_attempts_without_progress`: cate incercari consecutive fara progres sunt permise pentru acelasi subtip existent;
- `generation_limits.max_discovery_attempts_without_progress`: cate incercari consecutive fara progres sunt permise in etapa de descoperire;
- `generation_limits.max_failed_attempts_kept_per_scope`: cate incercari respinse sunt pastrate ca exemple negative in prompt;
- `ollama.model`: modelul local folosit pentru generare;
- `ollama.temperature`: nivelul de variabilitate al raspunsurilor;
- `terminal.show_ollama_prompt`: afisarea promptului complet in terminal;
- `terminal.show_ollama_response`: afisarea raspunsului brut in terminal;
- `terminal.show_ai_technical_messages`: afisarea mesajelor tehnice despre Ollama;
- `logging.save_ollama_chat`: salvarea dialogului complet in `logs/ollama_chat.log`;
- `logging.save_ollama_prompts`: salvarea prompturilor complete in `logs/ollama_prompts.log`;
- `logging.save_ollama_responses`: salvarea raspunsurilor brute in `logs/ollama_responses.log`.

Configurare recomandata pentru terminal curat:

```python
"terminal": {
    "show_ollama_prompt": False,
    "show_ollama_response": False,
    "show_ai_technical_messages": False,
}
```

Prompturile si raspunsurile complete raman salvate in `logs/`, fara sa incarce terminalul.

## 5. Fisierele de reguli

### `Rules.md`

Contine regulile generale aplicate tuturor prompturilor. Regulile stabilesc formatul raspunsului Ollama, cerinta de a genera o singura functie `test_*`, interdictia importurilor si cerinta de a folosi asertiuni exacte.

### `testing_functional.md`

Contine instructiuni numerotate pentru teste functionale. Testele functionale urmaresc comportamentul vizibil al functiei:

- valori valide;
- valori invalide;
- rezultate returnate;
- exceptii;
- valori limita;
- rezultate speciale;
- efectul argumentelor de tip flag sau boolean.

Fiecare linie numerotata este un subtip independent. Pentru fiecare subtip se genereaza teste cat timp exista progres. Dupa numarul configurat de incercari consecutive fara progres, se trece la subtipul urmator.

### `testing_structural.md`

Contine instructiuni numerotate pentru teste structurale. Testele structurale urmaresc caile de executie din cod:

- ramuri `if` si `else`;
- conditii simple;
- conditii compuse cu `and` / `or`;
- bucle cu zero, una sau mai multe iteratii;
- cai de exceptie;
- cai normale de returnare;
- cazuri in care o ramura ulterioara modifica sau nu modifica rezultatul.

## 6. Flux automat

Rulare principala:

```bash
python3 AutoTesting.py
```

Fluxul executat:

1. se curata fisierele temporare;
2. se verifica existenta conditiilor de rulare;
3. se citesc categoriile si subtipurile din `testing_*.md`;
4. pentru fiecare categorie se parcurg subtipurile existente;
5. pentru fiecare subtip se cer teste de la Ollama pana cand nu mai exista progres;
6. fiecare candidat este verificat cu `pytest`;
7. fiecare candidat valid este masurat cu `coverage.py` si `mutmut`;
8. candidatul este acceptat numai daca pastreaza `pytest` curat si imbunatateste cel putin un scor;
9. dupa acceptarea unui test, contorul de stagnare al subtipului se reseteaza;
10. dupa epuizarea subtipurilor existente, se intra in etapa de descoperire de teste noi;
11. daca un test nou acceptat poate fi sintetizat intr-o regula reutilizabila, regula este adaugata in fisierul `testing_*.md` corespunzator;
12. la final se afiseaza performanta testelor pe categorii si se arhiveaza rezultatele.

## 7. Rulare rapida cu script shell

Scripturile shell simplifica comenzile uzuale.

Activare drepturi de executie:

```bash
chmod +x run_auto.sh run_manual.sh
```

Rulare automata pe exemplul 1:

```bash
./run_auto.sh
```

Rulare automata pe exemplul 2:

```bash
./run_auto.sh 2
```

`run_auto.sh` executa:

```bash
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py Includes
python3 run_examples.py <numar_exemplu>
python3 AutoTesting.py
```

## 8. Rulare cu exemple

Listarea exemplelor disponibile:

```bash
python3 run_examples.py list
```

Pregatirea exemplului 1 fara pornirea framework-ului automat:

```bash
python3 run_examples.py 1
```

Pregatirea exemplului 1 si rularea framework-ului:

```bash
python3 run_examples.py 1 --run-autotesting
```

Rularea tuturor exemplelor:

```bash
python3 run_examples.py all --run-autotesting
```

`run_examples.py` copiaza `examples/<numar>/to_test.py` in root ca `to_test.py`, apoi ruleaza `reset.py` pentru a sterge testele generate anterior.

## 9. Resetarea workspace-ului

Resetare manuala:

```bash
python3 reset.py
```

Resetarea recreeaza fisierele de lucru:

- `test_functional.py`;
- `test_structural.py`;
- `test_propunere.py`.

Fiecare dintre aceste fisiere este resetat la scheletul minim:

```python
import pytest
from to_test import *
```

Resetarea mai sterge sau goleste:

- `Logs.jsonl`;
- `.coverage`;
- `.pytest_cache/`;
- `.mutmut-cache/`;
- `mutants/`;
- `__pycache__/`;
- logurile din `logs/`;
- artefactele temporare de rulare.

Fisierele `testing_functional.md` si `testing_structural.md` nu sunt sterse. Ele contin instructiunile de generare si trebuie pastrate.

## 10. Testare manuala in root

Rularea tuturor testelor finale din root:

```bash
python3 manual_testing.py all
```

Rularea testelor functionale:

```bash
python3 manual_testing.py functional
```

Rularea testelor structurale:

```bash
python3 manual_testing.py structural
```

Rulare cu stergerea artefactelor dupa finalizare:

```bash
python3 manual_testing.py all --clean-after
```

`manual_testing.py` ruleaza `pytest`, `coverage.py` cu branch coverage si `mutmut` pe selectia data. `test_propunere.py` este exclus din selectia `all`.

## 11. Testare manuala pe arhive

Dupa o rulare automata, fisierele finale sunt salvate in `arh/`.

Listarea arhivelor disponibile:

```bash
python3 run_arh_manual.py --list
```

Testarea ultimei arhive:

```bash
python3 run_arh_manual.py latest all
```

Testarea categoriei functionale din ultima arhiva:

```bash
python3 run_arh_manual.py latest functional
```

Testarea categoriei structurale din ultima arhiva:

```bash
python3 run_arh_manual.py latest structural
```

Rulare prin script shell:

```bash
./run_manual.sh latest all
./run_manual.sh latest functional
./run_manual.sh latest structural
```

Rulare pe arhiva numerotata:

```bash
./run_manual.sh 1 all
./run_manual.sh 2 functional
./run_manual.sh 3 structural
```

In interpretarea scriptului, `1` este cea mai veche arhiva disponibila, `2` este urmatoarea s.a.m.d. Valoarea `latest` selecteaza cea mai recenta arhiva.

## 12. Loguri

Logurile sunt pastrate in `logs/`:

```text
logs/framework.log          # log tehnic general
logs/events.jsonl           # evenimente structurale JSONL
logs/ollama_chat.log        # prompt + raspuns Ollama
logs/ollama_prompts.log     # prompturi complete
logs/ollama_responses.log   # raspunsuri brute Ollama
```

Terminalul este intentionat succint. Detaliile complete ale conversatiei cu Ollama se verifica in loguri.

Comenzi utile:

```bash
tail -n 40 logs/framework.log
tail -n 40 logs/ollama_responses.log
tail -n 40 logs/ollama_chat.log
```

## 13. Arhivare

La finalul unei rulari automate, aplicatia creeaza un subfolder in `arh/`, de forma:

```text
arh/1 12.05.2026 19:24/
```

In acest folder sunt salvate fisierele finale relevante, de exemplu:

- `to_test.py`;
- `test_functional.py`;
- `test_structural.py`.

Arhivele vechi pot fi sterse daca nu mai sunt necesare pentru comparatie sau raportare:

```bash
rm -rf arh/*
```

Comanda sterge toate arhivele existente si trebuie folosita numai cand rezultatele vechi nu mai sunt necesare.

## 14. Rezultate finale afisate

La finalul rularii se afiseaza un rezumat care include:

- numarul de teste acceptate pe categorie;
- performanta finala pentru `functional`;
- performanta finala pentru `structural`;
- scorurile `pytest`, `coverage` si `mutmut`;
- eventualele reguli noi adaugate in `testing_*.md`.

## 15. Recomandari pentru rulare curata

Rulare automata recomandata:

```bash
./run_auto.sh 1
```

Echivalent manual:

```bash
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py Includes
python3 run_examples.py 1
python3 AutoTesting.py
```

Verificarea ultimei arhive generate:

```bash
./run_manual.sh latest all
```

Echivalent manual:

```bash
python3 run_arh_manual.py latest all
```

## 16. Recomandari pentru GitHub

Pentru un repository curat, se recomanda pastrarea codului sursa, a fisierelor de reguli, a exemplelor si a scripturilor de rulare.

Se recomanda excluderea artefactelor generate automat:

```text
__pycache__/
.pytest_cache/
.mutmut-cache/
mutants/
htmlcov/
.coverage
logs/*.log
logs/*.jsonl
arh/
```

Daca rezultatele unei rulari trebuie demonstrate, un folder selectat din `arh/` poate fi pastrat separat sau atasat ca artefact, nu neaparat versionat permanent in repository.

## 17. Autor

Condruz Filip Gabriel  
Universitatea din Bucuresti, Facultatea de Matematica si Informatica, anul 3 ID
