import random
import pathlib

import pandas as pd
from shiny import App, reactive, render, ui

APP_DIR = pathlib.Path(__file__).parent

app_ui = ui.page_fillable(
    ui.tags.head(
        ui.tags.title("MSS Grant Lottery"),
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
                "In modelling and simulation science, ",
                ui.tags.a("PPS sampling", href="https://en.wikipedia.org/wiki/Probability-proportional-to-size_sampling", target="_blank"),
                " selects samples with probabilities proportional to a measure of size or relevance, "
                "ensuring every unit has a chance of selection. "
                "We applied the same principle to our travel grants: every eligible application "
                "entered the draw, while stronger alignment with the programme objectives increased "
                "the probability of selection.",
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
    )
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

        if any(w < 0 for w in weights):
            ui.notification_show("Scores must be non-negative.", type="error")
            return
        if sum(weights) == 0:
            ui.notification_show("At least one score must be greater than zero.", type="error")
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
        yield (APP_DIR.parent / "dummy_applicants.xlsx").read_bytes()

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