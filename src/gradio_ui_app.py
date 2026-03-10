# ui_app.py
import gradio as gr

from src.schemas import TimePreferences, BudgetLevel, Language
from event_client import run_dion_stream


def build_ui() -> gr.Blocks:
    time_choices = [tp.value for tp in TimePreferences]
    budget_choices = ['not set'] + [bl.value for bl in BudgetLevel]
    lang_choices = [l.value for l in Language]

    with gr.Blocks(title = 'BlastIn - Dion Test UI') as demo:
        gr.Markdown('# BlastIn – Dion (Planner + Reporter)')

        with gr.Accordion('Setup (API Key / Model)', open = True):
            openai_key = gr.Textbox(
                label = 'OPENAI_API_KEY (optional, sonst aus .env)',
                type = 'password',
                placeholder = 'sk-...',
            )
            model_name = gr.Dropdown(
                label = 'Model',
                choices = ['gpt-4.1-nano', 'gpt-4.1-mini', 'gpt-4.1'],
                value = 'gpt-4.1-nano',
            )

        with gr.Accordion('User / Trip', open = True):
            user_name = gr.Textbox(label = 'Name (optional)', placeholder = 'Adriana')

            with gr.Row():
                city = gr.Textbox(label = 'City', placeholder = 'Berlin')
                country = gr.Textbox(label = 'Country (optional)', placeholder = 'Deutschland')

            with gr.Row():
                date_start = gr.Date(label = 'Start date')
                date_end = gr.Date(label = 'End date')

            group_size = gr.Number(label = 'Group size (optional)', precision = 0)

        with gr.Accordion('Budget (optional)', open = False):
            budget_level = gr.Dropdown(label = 'Budget level', choices = budget_choices, value = 'not set')
            with gr.Row():
                budget_min = gr.Number(label = 'Min total (EUR)', precision = 0)
                budget_max = gr.Number(label = 'Max total (EUR)', precision = 0)

        with gr.Accordion('Event Preferences', open = True):
            with gr.Row():
                vibe = gr.Textbox(label = 'Vibe (optional)', placeholder = 'techno, hiphop, rnb')
                categories = gr.Textbox(label = 'Categories (optional)', placeholder = 'festival, concert, musical')

            with gr.Row():
                time_pref = gr.Dropdown(label = 'Time preference', choices = time_choices, value = TimePreferences.any.value)
                free_only = gr.Checkbox(label = 'Free events only', value = False)

        with gr.Accordion('Itinerary Preferences', open = False):
            must_avoid = gr.Textbox(
                label = 'Must avoid (optional) – comma/newline separated',
                placeholder = 'museum\nlong queues\nexpensive clubs',
                lines = 4,
            )

        with gr.Accordion('Delivery', open = False):
            language = gr.Dropdown(label = 'Output language', choices = lang_choices, value = Language.en.value)
            send_email = gr.Checkbox(label = 'Send email (keine API aktuell, aber Schema-Test)', value = False)
            email = gr.Textbox(label = 'Email (required if send_email = True)', placeholder = 'name@example.com')

        run_btn = gr.Button('Run Dion', variant = 'primary')

        gr.Markdown('---')

        with gr.Row():
            status_md = gr.Markdown(value = '_Waiting…_')

        with gr.Tabs():
            with gr.Tab('UI Output'):
                recommendation_out = gr.Markdown(label = 'Recommendation')
                events_out = gr.Dataframe(
                    headers = ['name', 'start_datetime', 'venue/area', 'price', 'ticket_url', 'source_url', 'event_id'],
                    label = 'Top Events',
                    interactive = False,
                    wrap = True,
                )
                spots_out = gr.Dataframe(
                    headers = ['name', 'address', 'entry_fee', 'opening_hours', 'source_url'],
                    label = 'Sightseeing Spots',
                    interactive = False,
                    wrap = True,
                )
                itinerary_out = gr.Markdown(label = 'Itinerary')

            with gr.Tab('Report'):
                report_out = gr.Markdown(label = 'Rendered Markdown Report')
                report_file = gr.File(label = 'Saved report file')

            with gr.Tab('Debug'):
                core_json_out = gr.Code(label = 'CoreResult JSON', language = 'json')
                report_json_out = gr.Code(label = 'MarkdownReport JSON', language = 'json')

        # WICHTIG:
        # Die Status-Zeilen:
        # ✅ City Keys geladen
        # 🔎 Events werden abgerufen…
        # 🧠 Plan wird gebaut…
        # 📝 Report wird gespeichert…
        #
        # ...werden NICHT hier erzeugt, sondern in event_client.run_dion_stream()
        # und erscheinen hier im status_md Output, weil run_dion_stream sie streamed.

        run_btn.click(
            fn = run_dion_stream,
            inputs = [
                openai_key,
                model_name,
                user_name,
                city,
                country,
                date_start,
                date_end,
                group_size,
                budget_level,
                budget_min,
                budget_max,
                vibe,
                categories,
                time_pref,
                free_only,
                must_avoid,
                language,
                send_email,
                email,
            ],
            outputs = [
                status_md,
                recommendation_out,
                events_out,
                spots_out,
                itinerary_out,
                report_out,
                report_file,
                core_json_out,
                report_json_out,
            ],
        )

        demo.queue()

    return demo


if __name__ == '__main__':
    app = build_ui()
    app.launch(server_name = '0.0.0.0', server_port = 7860)

