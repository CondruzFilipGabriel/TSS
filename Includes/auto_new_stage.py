from __future__ import annotations


class AutoNewStageMixin:
    def gaseste_teste_noi(self) -> None:
        """
        Etapa 2: cauta teste noi dupa epuizarea subtipurilor existente.

        Reguli:
        - se masoara doar timpul de generatie AI pentru bugetul pe categorie;
        - evaluarea se face pe testele categoriei + test_propunere.py;
        - daca o propunere valida imbunatateste categoria, este acceptata;
        - daca o propunere este acceptata, limita de timp AI pe categorie se reseteaza;
        - daca se acumuleaza limita configurata de iteratii consecutive fara imbunatatire,
          cautarea se opreste pentru categoria curenta;
        - aceeasi functie deja respinsa nu mai este rescored;
        - daca testul acceptat produce o regula reutilizabila, regula este salvata;
        - daca regula nu poate fi sintetizata, testul ramane acceptat fara regula noua.
        """
        self.logger.section("Etapa 2:")
        self.logger.console_step("caut teste noi care imbunatatesc performanta")

        stage_name = "discovery"

        try:
            for testing_md_path in self.fisiere_testing_md:
                category = self.workspace.get_category_name_from_testing_md(
                    testing_md_path
                )
                self.logger.console_step(f"procesez categoria {category}")
                self.generated_tests_by_category.setdefault(category, 0)
                self.accepted_tests_by_category.setdefault(category, 0)
                category_generated_before_discovery = self.generated_tests_by_category.get(category, 0)

                category_test_file = self.workspace.map_testing_md_to_test_py(
                    testing_md_path
                )
                category_selected_test_files = [category_test_file.name]
                self.logger.log_category_start(
                    stage=stage_name,
                    category=category,
                    test_file_name=category_test_file.name,
                )

                if self.tests_performance.has_any_tests(category_selected_test_files):
                    initial_category_scores = self.get_current_scores(
                        category_selected_test_files
                    )
                    if self.log_maximum_score_if_reached(
                        category=category,
                        scores=initial_category_scores,
                    ):
                        reason = "categoria are deja scor maxim"
                        self.logger.debug(
                            f"Categoria {category} este sarita in etapa de teste noi deoarece are deja scor maxim."
                        )
                        self.logger.log_category_skip(
                            stage=stage_name,
                            category=category,
                            reason=reason,
                            scores=initial_category_scores,
                        )
                        continue

                ai_budget_ramas = float(
                    self.config.timeouts.timeout_categorie_ai_sec
                )

                max_iterations_without_improvement = self.config.generation_limits.max_discovery_attempts_without_progress
                iterations_without_improvement = 0
                discovery_attempt_number = 1

                self.logger.console_step(
                    f"incerc generarea de teste noi pentru categoria {category}..."
                )

                while ai_budget_ramas > 0:
                    self.logger.debug(
                        f"Buget AI ramas pentru {category}: {round(ai_budget_ramas, 2)}s"
                    )
                    self.logger.debug(
                        f"Iteratii consecutive fara imbunatatire pentru {category}: "
                        f"{iterations_without_improvement}/{max_iterations_without_improvement}"
                    )

                    if iterations_without_improvement >= max_iterations_without_improvement:
                        warning_message = (
                            f"Categoria {category} este oprita deoarece au fost atinse "
                            f"{max_iterations_without_improvement} iteratii consecutive "
                            f"fara nicio imbunatatire."
                        )
                        self.logger.warning(warning_message)
                        self.logger.log_stagnation_stop(
                            stage=stage_name,
                            category=category,
                            attempts_without_progress=iterations_without_improvement,
                        )
                        break

                    before_scores = self.get_current_scores(category_selected_test_files)
                    category_has_tests = self.tests_performance.has_any_tests(
                        category_selected_test_files
                    )

                    if (
                        category_has_tests
                        and self.log_maximum_score_if_reached(
                            category=category,
                            scores=before_scores,
                        )
                    ):
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

                    self.logger.debug(
                        f"Scoruri curente pentru categoria {category} ({category_test_file.name}) -> "
                        f"{self.format_scores_for_debug(before_scores)}"
                    )
                    self.logger.log_attempt_start(
                        stage=stage_name,
                        category=category,
                        attempt_number=discovery_attempt_number,
                        attempts_without_progress=iterations_without_improvement,
                        max_attempts_without_progress=max_iterations_without_improvement,
                        scores_before=before_scores,
                        ai_budget_remaining_sec=round(ai_budget_ramas, 2),
                    )

                    current_attempt_number = discovery_attempt_number
                    valid_function, ai_consumed = self.solicita_functie_valida(
                        testing_md_path=testing_md_path,
                        bullet_index=None,
                        remaining_ai_budget_sec=ai_budget_ramas,
                        failed_attempts=self.get_failed_attempts_for_category(category),
                        attempt_number=current_attempt_number,
                        attempts_without_progress=iterations_without_improvement,
                        max_attempts_without_progress=max_iterations_without_improvement,
                        performance_summary=self.format_scores_for_debug(before_scores),
                    )

                    discovery_attempt_number += 1
                    ai_budget_ramas -= ai_consumed

                    if not valid_function:
                        rejection_reason = (
                            "Nu a fost obtinuta nicio propunere valida in bugetul ramas "
                            "sau in tentativele disponibile."
                        )
                        self.logger.debug(rejection_reason)
                        self.logger.log_attempt_invalid(
                            stage=stage_name,
                            category=category,
                            attempt_number=current_attempt_number,
                            reason=rejection_reason,
                        )
                        iterations_without_improvement += 1

                        if ai_budget_ramas <= 0:
                            break

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
                        )
                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.remember_rejected_hash(
                            category=category,
                            function_code=valid_function,
                        )
                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1
                        continue

                    if self.has_rejected_hash(category, valid_function):
                        rejection_reason = (
                            "Propunerea este respinsa deoarece aceasta functie a mai fost "
                            "evaluata si respinsa anterior in aceasta categorie."
                        )
                        self.logger.debug(rejection_reason)
                        self.logger.log_attempt_rejected(
                            stage=stage_name,
                            category=category,
                            function_name=function_name,
                            reason=rejection_reason,
                            before_scores=before_scores,
                        )
                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1
                        continue

                    self.workspace.overwrite_proposal_with_function(valid_function)

                    candidate_selected_test_files = self.build_candidate_selected_test_files(
                        category_test_file_name=category_test_file.name
                    )

                    after_scores = self.get_current_scores(candidate_selected_test_files)

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
                        self.workspace.append_extension_function_to_test_file(
                            test_file_path=category_test_file,
                            function_code=valid_function,
                        )

                        rule, reasoning = self.solicita_rule_si_reasoning(
                            testing_md_path=testing_md_path,
                            accepted_function=valid_function,
                        )

                        improvement = self.tests_performance.format_improvement(
                            before_scores=before_scores,
                            after_scores=after_scores,
                        )

                        rule_was_saved = self.salveaza_regula_acceptata_daca_exista(
                            category=category,
                            testing_md_path=testing_md_path,
                            rule=rule,
                            reasoning=reasoning,
                            improvement=improvement,
                        )

                        self.logger.log_attempt_accepted(
                            stage=stage_name,
                            category=category,
                            function_name=function_name,
                            before_scores=before_scores,
                            after_scores=after_scores,
                            rule_saved=rule_was_saved,
                        )
                        self.logger.log_rule_result(
                            category=category,
                            rule_saved=rule_was_saved,
                            reasoning=reasoning,
                            rule=rule,
                        )

                        if rule_was_saved:
                            self.numar_reguli_adaugate += 1

                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()

                        ai_budget_ramas = float(
                            self.config.timeouts.timeout_categorie_ai_sec
                        )
                        iterations_without_improvement = 0

                        self.logger.debug(
                            f"Bugetul AI pentru {category} a fost resetat dupa acceptarea propunerii."
                        )
                        self.logger.debug(
                            f"Contorul de stagnare pentru {category} a fost resetat la 0."
                        )

                        if self.log_maximum_score_if_reached(
                            category=category,
                            scores=after_scores,
                        ):
                            break
                    else:
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
                        )

                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.remember_rejected_hash(
                            category=category,
                            function_code=valid_function,
                        )

                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1

                accepted_in_discovery = (
                    self.generated_tests_by_category.get(category, 0)
                    - category_generated_before_discovery
                )
                self.logger.console_step(
                    f"cautare finalizata pentru {category}. Teste acceptate: {accepted_in_discovery}"
                )

        finally:
            self.ollama_client.stop()
