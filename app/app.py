import random
import pathlib

import pandas as pd
from shiny import App, reactive, render, ui

APP_DIR = pathlib.Path(__file__).parent

app_ui = ui.page_fillable(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="styles.css"),
        ui.tags.script(src="confetti.browser.min.js"),
        ui.tags.script(src="confetti_handler.js"),
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.div(
                ui.h4("MSS Grant Lottery", class_="d-inline"),
                ui.input_action_button(
                    "reset_btn", "Reset", class_="btn-outline-secondary btn-sm float-end"
                ),
            ),
            ui.p(
                "In modeling and simulation sciences, ",
                ui.tags.a("importance sampling", href="https://en.wikipedia.org/wiki/Importance_sampling", target="_blank"),
                " increases the probability of drawing informative samples without excluding the "
                "rest of the population. Inspired by that same idea, our travel grant lottery gives "
                "every eligible applicant a place in the draw, while stronger alignment with the "
                "programme objectives increases their odds of selection.",
                style="font-size:0.72rem; color:#6c757d; margin-top:0.4rem; margin-bottom:0;",
            ),
            ui.output_ui("upload_card"),
            ui.output_ui("config_panel"),
            ui.output_ui("lottery_panel"),
            ui.div(
                ui.tags.img(src="rwth_mss_bild_rgb.svg", style="max-width:100%; margin-bottom:0.5rem;"),
                ui.p(
                    "Developed by ",
                    ui.tags.a("Alan Correa", href="https://github.com/thealanjason", target="_blank"),
                    " ",
                    ui.tags.a(
                        ui.HTML(
                            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
                            'width="14" height="14" fill="currentColor" style="vertical-align:-2px;">'
                            '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
                            '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
                            '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
                            '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
                            '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
                            '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>'
                            '</svg>'
                        ),
                        href="https://github.com/mss-rwth/mss-grant-lottery",
                        target="_blank",
                        title="Source on GitHub",
                        style="color:inherit;",
                    ),
                    style="margin:0; font-size:0.72rem;",
                ),
                class_="sidebar-footer",
            ),
            width=340,
            open="always",
        ),
        ui.card(
            ui.card_header("Applicants"),
            ui.output_data_frame("applicants_table"),
            fill=True,
        ),
        ui.output_ui("result_panel"),
        fill=True,
        fillable=True,
    ),
)


def server(input, output, session):
    df = reactive.Value(None)
    selected_names = reactive.Value(None)
    reset_counter = reactive.Value(0)

    @render.ui
    def upload_card():
        reset_counter()  # dependency forces re-render on reset, clearing the file input
        return ui.div(
            ui.hr(),
            ui.input_file("file", "Upload Applicant Data (.xlsx / .xls)", accept=[".xlsx", ".xls"]),
            ui.download_button("example_btn", "Download example", class_="btn-link btn-sm p-0 example-download"),
        )

    @reactive.effect
    @reactive.event(input.reset_btn)
    def do_reset():
        df.set(None)
        selected_names.set(None)
        reset_counter.set(reset_counter() + 1)

    @reactive.effect
    @reactive.event(input.file)
    def load_file():
        file_info = input.file()
        if not file_info:
            return
        path = file_info[0]["datapath"]
        try:
            data = pd.read_excel(path)
            df.set(data)
            selected_names.set(None)
        except Exception as e:
            ui.notification_show(f"Error reading file: {e}", type="error")

    @render.ui
    def config_panel():
        data = df()
        if data is None:
            return ui.div()
        cols = data.columns.tolist()
        return ui.div(
            ui.div(
                ui.div(ui.input_select("name_col", "Name column", choices=cols, selected=cols[0]), style="flex:1;"),
                ui.div(ui.input_select("score_col", "Score column", choices=cols, selected=cols[-1]), style="flex:1;"),
                style="display:flex; gap:0.5rem;",
            ),
            class_="settings-panel",
        )

    @render.ui
    def lottery_panel():
        if df() is None:
            return ui.div()
        return ui.div(
            ui.hr(),
            ui.input_select(
                "n_select",
                "Number of applicants to select",
                choices=[str(i) for i in range(1, 11)],
                selected="1",
            ),
            ui.input_action_button(
                "select_btn", "Select Applicant(s)", class_="btn-primary w-100 mt-2"
            ),
        )

    @render.data_frame
    def applicants_table():
        data = df()
        if data is None:
            return pd.DataFrame()
        return render.DataGrid(data, width="100%")

    @reactive.effect
    @reactive.event(input.select_btn)
    async def run_lottery():
        data = df()
        if data is None:
            return

        score_col = input.score_col()
        name_col = input.name_col()
        n = min(int(input.n_select()), len(data))
        weights = data[score_col].tolist()

        if any(w <= 0 for w in weights):
            ui.notification_show("All scores must be greater than zero.", type="error")
            return

        names = data[name_col].tolist()
        chosen = _weighted_sample_without_replacement(names, weights, n)
        selected_names.set(chosen)
        await session.send_custom_message("fire_confetti", {})

    @render.ui
    def result_panel():
        names = selected_names()
        if names is None:
            return ui.div()
        applicant_cards = [
            ui.card(
                ui.card_body(
                    ui.div(ui.tags.strong(str(name))),
                    ui.p(f"#{i + 1}", class_="rank fw-bold"),
                ),
                class_="result-applicant-card",
            )
            for i, name in enumerate(names)
        ]
        return ui.card(
            ui.card_header(
                ui.div(
                    ui.tags.strong("Selected Applicant(s)"),
                    ui.download_button("download_btn", "Download (.txt)", class_="btn-sm ms-2"),
                    style="display:flex; align-items:center;",
                )
            ),
            ui.div(
                *applicant_cards,
                style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem; padding: 0.75rem;",
            ),
            class_="result-card shadow",
            fill=False,
        )

    @render.download(filename="dummy_applicants.xlsx")
    async def example_btn():
        yield (APP_DIR / "dummy_applicants.xlsx").read_bytes()

    @render.download(filename="selected_applicants.txt")
    async def download_btn():
        names = selected_names()
        if names is None:
            return
        yield "\n".join(str(name) for name in names)


def _weighted_sample_without_replacement(population, weights, k):
    indices = list(range(len(population)))
    wts = list(weights)
    selected = []
    for _ in range(k):
        chosen_pos = random.choices(range(len(indices)), weights=wts, k=1)[0]
        selected.append(population[indices[chosen_pos]])
        indices.pop(chosen_pos)
        wts.pop(chosen_pos)
    return selected


app = App(app_ui, server, static_assets=APP_DIR)