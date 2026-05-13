from __future__ import annotations


class AutoInitialStageMixin:
    def scrie_teste_initiale(self) -> None:
        """
        Etapa 1: parcurge subtipurile explicite din fiecare fisier
        testing_*.md si genereaza teste pentru fiecare subtip cat timp exista
        progres masurabil.

        Logica principala:
        - subtipurile initiale sunt deja definite in testing_*.md;
        - modelul primeste un singur subtip concret si genereaza o functie de
          test care trebuie sa apartina acelui subtip;
        - acelasi subtip poate produce mai multe teste acceptate;
        - o propunere este acceptata doar daca imbunatateste scorurile
          categoriei, fara sa strice pytest;
        - pentru fiecare subtip, fluxul se opreste dupa limita configurata de incercari
          consecutive fara progres.
        """
        self.logger.section("Etapa 1:")
        self.logger.console_step("generez teste pe subtipurile existente")

        max_attempts_without_progress = self.config.generation_limits.max_existing_subtype_attempts_without_progress
        stage_name = "initial"

        try:
            for testing_md_path in self.fisiere_testing_md:
                category = self.workspace.get_category_name_from_testing_md(
                    testing_md_path
                )
                self.logger.console_step(f"procesez categoria {category}")
                self.generated_tests_by_category.setdefault(category, 0)
                self.accepted_tests_by_category.setdefault(category, 0)

                bullets = self.workspace.extract_testing_rule_bullets(
                    testing_md_path
                )
                if not bullets:
                    warning_message = (
                        f"Categoria {category} nu are subtipuri definite in "
                        f"{testing_md_path.name}."
                    )
                    self.logger.warning(warning_message)
                    self.logger.log_category_skip(
                        stage=stage_name,
                        category=category,
                        reason=warning_message,
                    )
                    continue

                category_test_file = self.workspace.map_testing_md_to_test_py(
                    testing_md_path
                )
                category_selected_test_files = [category_test_file.name]
                self.logger.log_category_start(
                    stage=stage_name,
                    category=category,
                    test_file_name=category_test_file.name,
                )

                category_complete = False
                if self.tests_performance.has_any_tests(category_selected_test_files):
                    initial_category_scores = self.get_current_scores(
                        category_selected_test_files
                    )
                    category_complete = self.log_maximum_score_if_reached(
                        category=category,
                        scores=initial_category_scores,
                    )
                else:
                    initial_category_scores = None

                if category_complete:
                    reason = "categoria are deja scor maxim"
                    self.logger.debug(
                        f"Categoria {category} este sarita in etapa initiala deoarece are deja scor maxim."
                    )
                    self.logger.log_category_skip(
                        stage=stage_name,
                        category=category,
                        reason=reason,
                        scores=initial_category_scores,
                    )
                    continue

                for bullet_index, bullet_text in enumerate(bullets):
                    if category_complete:
                        break

                    subtype_number = bullet_index + 1
                    subtype_key = f"{category}:subtype_{subtype_number}"
                    attempts_without_progress = 0
                    attempt_number = 1
                    subtype_accepted_count = 0
                    subtype_failed_attempts: list[tuple[str, str]] = []

                    self.logger.console_step(
                        f"subtip {subtype_number}/{len(bullets)} ({category}): {bullet_text}"
                    )
                    self.logger.console_step("incerc generarea pentru acest subtip...")
                    self.logger.debug(
                        f"Subtip curent pentru {category}: {bullet_text}"
                    )
                    self.logger.log_subtype_start(
                        category=category,
                        subtype_number=subtype_number,
                        total_subtypes=len(bullets),
                        subtype_text=bullet_text,
                    )

                    while attempts_without_progress < max_attempts_without_progress:
                        current_attempt_number = attempt_number
                        category_has_tests = self.tests_performance.has_any_tests(
                            category_selected_test_files
                        )
                        before_scores = self.get_current_scores(
                            category_selected_test_files
                        )

                        if (
                            category_has_tests
                            and self.log_maximum_score_if_reached(
                                category=category,
                                scores=before_scores,
                            )
                        ):
                            category_complete = True
                            self.logger.log_category_skip(
                                stage=stage_name,
                                category=category,
                                reason="categoria a atins scor maxim inaintea incercarii curente",
                                scores=before_scores,
                            )
                            break

                        if (
                            category_has_tests
                            and not self.tests_performance.is_pytest_clean(before_scores)
                        ):
                            warning_message = (
                                f"Categoria {category} nu poate continua deoarece "
                                "suita curenta nu este curata la pytest."
                            )
                            self.logger.warning(warning_message)
                            self.logger.log_category_skip(
                                stage=stage_name,
                                category=category,
                                reason=warning_message,
                                scores=before_scores,
                            )
                            break

                        performance_summary = (
                            f"Current category scores before candidate: "
                            f"{self.format_scores_for_debug(before_scores)}\n"
                            "Acceptance rule: keep pytest clean and improve at least one score."
                        )

                        self.logger.debug(
                            f"Incercare {current_attempt_number} pentru subtipul {subtype_number} "
                            f"din categoria {category}. Fara progres: "
                            f"{attempts_without_progress}/{max_attempts_without_progress}."
                        )
                        self.logger.debug(
                            f"Scoruri curente pentru categoria {category} -> "
                            f"{self.format_scores_for_debug(before_scores)}"
                        )
                        self.logger.log_attempt_start(
                            stage=stage_name,
                            category=category,
                            attempt_number=current_attempt_number,
                            attempts_without_progress=attempts_without_progress,
                            max_attempts_without_progress=max_attempts_without_progress,
                            scores_before=before_scores,
                            subtype_number=subtype_number,
                            subtype_text=bullet_text,
                        )

                        valid_function, _ = self.solicita_functie_valida(
                            testing_md_path=testing_md_path,
                            bullet_index=bullet_index,
                            failed_attempts=subtype_failed_attempts,
                            attempt_number=current_attempt_number,
                            attempts_without_progress=attempts_without_progress,
                            max_attempts_without_progress=max_attempts_without_progress,
                            performance_summary=performance_summary,
                        )

                        attempt_number += 1

                        if not valid_function:
                            rejection_reason = (
                                "Nu a fost obtinuta nicio functie valida pentru "
                                "subtipul curent."
                            )
                            self.logger.debug(rejection_reason)
                            self.logger.log_attempt_invalid(
                                stage=stage_name,
                                category=category,
                                attempt_number=current_attempt_number,
                                reason=rejection_reason,
                                subtype_number=subtype_number,
                            )
                            subtype_failed_attempts.append(
                                ("# Empty or invalid answer", rejection_reason)
                            )
                            if len(subtype_failed_attempts) > self.config.generation_limits.max_failed_attempts_kept_per_scope:
                                del subtype_failed_attempts[:-self.config.generation_limits.max_failed_attempts_kept_per_scope]
                            self.workspace.clear_proposal_test_file()
                            self.ollama_client.reset_context()
                            attempts_without_progress += 1
                            continue

                        function_name = self.response_parser.extract_function_name(
                            valid_function
                        )

                        if self.workspace.function_exists_in_file(
                            file_path=category_test_file,
                            function_name=function_name,
                        ):
                            rejection_reason = (
                                f"Propunerea este respinsa deoarece functia {function_name} "
                                f"exista deja in {category_test_file.name}."
                            )
                            self.logger.debug(rejection_reason)
                            self.logger.log_attempt_rejected(
                                stage=stage_name,
                                category=category,
                                function_name=function_name,
                                reason=rejection_reason,
                                before_scores=before_scores,
                                subtype_number=subtype_number,
                            )
                            subtype_failed_attempts.append((valid_function, rejection_reason))
                            self.remember_rejected_hash(
                                category=subtype_key,
                                function_code=valid_function,
                            )
                            self.workspace.clear_proposal_test_file()
                            self.ollama_client.reset_context()
                            attempts_without_progress += 1
                            continue

                        if self.has_rejected_hash(subtype_key, valid_function):
                            rejection_reason = (
                                "Propunerea este respinsa deoarece aceeasi functie "
                                "a mai fost evaluata si respinsa pentru acest subtip."
                            )
                            self.logger.debug(rejection_reason)
                            self.logger.log_attempt_rejected(
                                stage=stage_name,
                                category=category,
                                function_name=function_name,
                                reason=rejection_reason,
                                before_scores=before_scores,
                                subtype_number=subtype_number,
                            )
                            subtype_failed_attempts.append((valid_function, rejection_reason))
                            self.workspace.clear_proposal_test_file()
                            self.ollama_client.reset_context()
                            attempts_without_progress += 1
                            continue

                        self.workspace.overwrite_proposal_with_function(valid_function)

                        candidate_selected_test_files = self.build_candidate_selected_test_files(
                            category_test_file_name=category_test_file.name
                        )
                        after_scores = self.get_current_scores(
                            candidate_selected_test_files
                        )

                        self.logger.debug(
                            f"Scoruri candidat pentru categoria {category} "
                            f"({candidate_selected_test_files}) -> "
                            f"{self.format_scores_for_debug(after_scores)}"
                        )
                        self.logger.log_candidate_scores(
                            stage=stage_name,
                            category=category,
                            selected_test_files=candidate_selected_test_files,
                            scores_after=after_scores,
                            subtype_number=subtype_number,
                        )

                        should_accept = self.should_accept_stage2_proposal(
                            category_has_tests_before=category_has_tests,
                            before_scores=before_scores,
                            after_scores=after_scores,
                        )

                        if should_accept:
                            self.generated_tests_by_category[category] = (
                                self.generated_tests_by_category.get(category, 0) + 1
                            )
                            self.accepted_tests_by_category[category] = (
                                self.accepted_tests_by_category.get(category, 0) + 1
                            )
                            subtype_accepted_count += 1
                            self.logger.log_attempt_accepted(
                                stage=stage_name,
                                category=category,
                                function_name=function_name,
                                before_scores=before_scores,
                                after_scores=after_scores,
                                subtype_number=subtype_number,
                            )
                            self.workspace.append_function_to_test_file(
                                test_file_path=category_test_file,
                                function_code=valid_function,
                            )
                            self.workspace.clear_proposal_test_file()
                            self.ollama_client.reset_context()
                            attempts_without_progress = 0

                            self.logger.debug(
                                "Contorul de stagnare pentru subtipul curent a fost resetat la 0."
                            )

                            if self.log_maximum_score_if_reached(
                                category=category,
                                scores=after_scores,
                            ):
                                category_complete = True
                                break

                            continue

                        rejection_reason = self.explain_stage2_rejection_reason(
                            category_has_tests_before=category_has_tests,
                            before_scores=before_scores,
                            after_scores=after_scores,
                        )
                        self.logger.debug(rejection_reason)
                        self.logger.log_attempt_rejected(
                            stage=stage_name,
                            category=category,
                            function_name=function_name,
                            reason=rejection_reason,
                            before_scores=before_scores,
                            after_scores=after_scores,
                            subtype_number=subtype_number,
                        )

                        subtype_failed_attempts.append((valid_function, rejection_reason))
                        if len(subtype_failed_attempts) > self.config.generation_limits.max_failed_attempts_kept_per_scope:
                            del subtype_failed_attempts[:-self.config.generation_limits.max_failed_attempts_kept_per_scope]

                        self.remember_rejected_hash(
                            category=subtype_key,
                            function_code=valid_function,
                        )

                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        attempts_without_progress += 1

                    self.logger.debug(
                        f"Subtipul {subtype_number} din categoria {category} s-a incheiat "
                        f"dupa {attempts_without_progress} incercari consecutive fara progres."
                    )
                    self.logger.log_stagnation_stop(
                        stage=stage_name,
                        category=category,
                        subtype_number=subtype_number,
                        attempts_without_progress=attempts_without_progress,
                    )
                    self.logger.console_step(
                        f"subtip {subtype_number} finalizat. Teste acceptate: {subtype_accepted_count}"
                    )

                self.logger.console_step(
                    f"categoria {category} finalizata. Teste acceptate: "
                    f"{self.generated_tests_by_category.get(category, 0)}"
                )
                self.ollama_client.reset_context()

            self.workspace.add_final_comment_to_initial_test_files()

        finally:
            self.ollama_client.stop()
