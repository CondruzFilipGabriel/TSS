# =====================================================================
# config.py
# =====================================================================
# Configurarea principala a aplicatiei.
#
# Fisierul este Python, nu JSON, pentru ca permite comentarii clare.
# Structura este intentionat apropiata de JSON: o singura variabila CONFIG,
# impartita pe sectiuni. In mod normal, aici se modifica doar valori, nu cod.
# =====================================================================

CONFIG = {
    # ---------------------------------------------------------------
    # Limite pentru rulari externe si pentru raspunsurile Ollama
    # ---------------------------------------------------------------
    "timeouts": {
        # Timeout pentru comenzi obisnuite: pytest, coverage si apelul HTTP catre Ollama.
        # Valori mai mici: aplicatia renunta mai repede la comenzi blocate, dar poate opri
        #                  si raspunsuri Ollama lente, dar valide.
        # Valori mai mari: da mai mult timp modelului si comenzilor, dar poate face rularea
        #                   foarte lenta cand modelul sau un tool se blocheaza.
        # Foarte mic, ex. 5: risc mare de timeouts false.
        # Foarte mare, ex. 1000: o problema poate bloca mult timp etapa curenta.
        "timeout_sec": 180,

        # Timeout separat pentru mutmut, fiindca mutation testing este de obicei mai lent.
        # Mai mic: testare mai rapida, dar risc de oprire inainte de finalizarea mutantilor.
        # Mai mare: rezultate mai stabile, dar rularea poate dura mult.
        "timeout_sec_mutmut": 600,

        # Buget AI maxim pentru o categorie in etapa de descoperire.
        # Mai mic: trece mai repede peste categorii fara progres.
        # Mai mare: permite mai multe incercari, dar poate consuma mult timp.
        "timeout_categorie_ai_sec": 1800,

        # Cate corectii cere pentru o propunere invalida.
        # 0: nu cere corectii, trece imediat mai departe.
        # 1: recomandat pentru model local mic; evita bucle lungi.
        # Foarte mare: poate consuma multe minute pe aceeasi idee gresita.
        "max_corectie_attempts": 1,

        # Cate raspunsuri goale/inutilizabile consecutive accepta inainte sa renunte.
        # Prea mic: poate renunta dupa un singur rateu temporar.
        # Prea mare: poate pierde timp cu un model care nu respecta formatul.
        "max_empty_answers_consecutive": 2,
    },

    # ---------------------------------------------------------------
    # Limite pentru buclele de generare
    # ---------------------------------------------------------------
    "generation_limits": {
        # Pentru un subtip existent din testing_*.md, cate incercari consecutive
        # fara progres sunt permise inainte de trecerea la subtipul urmator.
        # 1: foarte rapid, dar poate sari peste subtipuri dupa un singur raspuns slab.
        # 3: echilibru bun pentru teste rapide cu model local.
        # 10+: cauta mai insistent, dar poate repeta aceleasi idei prea mult.
        "max_existing_subtype_attempts_without_progress": 3,

        # Pentru etapa de descoperire, cate incercari consecutive fara progres
        # sunt permise inainte de oprirea categoriei.
        # Mai mic: etapa 2 devine scurta si conservatoare.
        # Mai mare: poate descoperi cazuri rare, dar consuma timp.
        "max_discovery_attempts_without_progress": 3,

        # Cate incercari respinse sunt pastrate in prompt ca exemple negative.
        # Prea mic: modelul poate repeta aceeasi idee.
        # Prea mare: promptul devine lung si modelul local poate fi distras.
        "max_failed_attempts_kept_per_scope": 3,
    },

    # ---------------------------------------------------------------
    # Ollama
    # ---------------------------------------------------------------
    "ollama": {
        # Modelul local folosit pentru generarea testelor.
        "model": "qwen2.5-coder:7b",
        "host": "127.0.0.1",
        "port": 11434,
        "generate_endpoint": "/api/generate",
        "tags_endpoint": "/api/tags",
        "keep_alive": "5m",

        # Temperatura mai mica produce raspunsuri mai stabile si mai putin creative.
        # 0.0-0.2: recomandat pentru cod si teste concrete.
        # 0.7+: mai creativ, dar risc mai mare de format gresit sau asertiuni inventate.
        "temperature": 0.1,

        # Cat asteapta aplicatia ca API-ul Ollama sa raspunda.
        "api_ready_timeout_sec": 3,
        "start_wait_timeout_sec": 20,
        "start_poll_interval_sec": 0.5,
    },

    # ---------------------------------------------------------------
    # Terminal si loguri
    # ---------------------------------------------------------------
    "terminal": {
        # Afiseaza promptul complet trimis catre Ollama.
        # True: util pentru diagnosticarea instructiunilor neintelese.
        # False: terminal mult mai curat, dar trebuie consultat logs/ollama_chat.log.
        "show_ollama_prompt": False,

        # Afiseaza raspunsul brut primit de la Ollama.
        # True: util cand se regleaza prompturile.
        # False: recomandat pentru rularea normala, deoarece raspunsurile pot fi lungi.
        "show_ollama_response": False,

        # Afiseaza mesajele tehnice despre pornire API, reset context, timp raspuns.
        # False: terminalul ramane concentrat pe etape, prompturi si rezultate.
        # True: util doar pentru debugging tehnic Ollama.
        "show_ai_technical_messages": False,
    },

    "logging": {
        # Salveaza fiecare prompt si raspuns Ollama impreuna, in logs/ollama_chat.log.
        # True este recomandat in perioada de reglare a prompturilor.
        "save_ollama_chat": True,

        # Salveaza prompturile complete, separat, in logs/ollama_prompts.log.
        # True: permite analiza exacta a instructiunilor trimise catre model.
        # False: reduce dimensiunea logurilor, dar face debugging-ul prompturilor mai greu.
        "save_ollama_prompts": True,

        # Salveaza raspunsurile brute, separat, in logs/ollama_responses.log.
        # True: permite verificarea tuturor propunerilor generate de model.
        # False: reduce logurile, dar ascunde raspunsurile respinse de validator.
        "save_ollama_responses": True,
    },
}
