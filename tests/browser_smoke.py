"""GitHub runner browser smoke test with all non-local browser requests blocked."""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = 'http://127.0.0.1:4452'


def run():
    subprocess.run([sys.executable, '-m', 'flask', 'db', 'upgrade'], check=True)
    subprocess.run([sys.executable, '-m', 'flask', 'seed-yeasts'], check=True)
    log_path = Path('.work/browser-server.log')
    log_path.parent.mkdir(exist_ok=True)
    with log_path.open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'gunicorn', '--workers', '1',
                                   '--bind', '127.0.0.1:4452', '--no-control-socket', 'wsgi:app'],
                                  stdout=log, stderr=log)
        try:
            for _ in range(40):
                try:
                    urllib.request.urlopen(BASE + '/healthz', timeout=1).close()
                    break
                except OSError:
                    if server.poll() is not None:
                        raise RuntimeError('Browser test server exited')
                    time.sleep(0.5)
            else:
                raise RuntimeError('Browser test server did not become ready')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                errors, external = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def local_only(route):
                    if route.request.url.startswith(BASE + '/'):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()
                page.route('**/*', local_only)
                page.goto(BASE + '/setup')
                page.locator('[name=username]').fill('browser-admin')
                page.locator('[name=password]').fill('Browser1!Password')
                page.locator('[name=confirm_password]').fill('Browser1!Password')
                page.get_by_role('button', name='Create Admin Account').click()
                page.wait_for_url('**/app/')
                page.get_by_role('link', name='Settings').click()
                page.get_by_role('button', name='Logout').click()
                page.wait_for_url('**/login')
                page.locator('[name=username]').fill('browser-admin')
                page.locator('[name=password]').fill('Browser1!Password')
                page.get_by_role('button', name='Log In').click()
                page.wait_for_url('**/app/')

                page.goto(BASE + '/app/recipes/new')
                page.locator('[name=name]').fill('Offline cider')
                page.locator('[name=alcohol_type]').select_option('Hard Cider')
                assert page.evaluate("() => !quill.options.formats.includes('video') && !quill.options.formats.includes('formula')")
                page.evaluate("() => quill.clipboard.dangerouslyPasteHTML('<p>No embeds</p><iframe src=\"https://example.test/video\"></iframe>')")
                assert page.locator('.ql-editor iframe, .ql-editor .ql-formula').count() == 0
                page.evaluate("""() => quill.clipboard.dangerouslyPasteHTML(
                    '<p><strong>Mix safely</strong></p><ul><li>Keep this bullet</li></ul>')""")
                for i in range(3):
                    if i:
                        page.get_by_role('button', name='Add Ingredient').click()
                    page.locator(f'[name=ingredient_name_{i}]').fill(f'Ingredient {i}')
                    page.locator(f'[name=ingredient_amount_{i}]').fill(str(i + 1))
                    page.locator(f'[name=ingredient_unit_{i}]').fill('g')
                page.get_by_role('button', name='Create Recipe').click()
                page.wait_for_url('**/app/')
                page.get_by_role('link', name='Offline cider', exact=True).click()
                recipe_url = page.url
                expect(page.locator('.recipe-instructions strong')).to_have_text('Mix safely')
                expect(page.locator('.recipe-instructions ul li')).to_have_text('Keep this bullet')

                page.goto(recipe_url + '/edit')
                expect(page.locator('.ql-editor')).to_contain_text('Mix safely')
                page.once('dialog', lambda dialog: dialog.accept())
                page.locator('.ingredient-row').first.get_by_role('button').click()
                page.get_by_role('button', name='Save Changes').click()
                page.wait_for_url(recipe_url)
                expect(page.locator('main')).not_to_contain_text('Ingredient 0')
                expect(page.locator('main')).to_contain_text('Ingredient 1')
                expect(page.locator('.recipe-instructions ul li')).to_have_text('Keep this bullet')

                page.goto(BASE + '/app/batches/new')
                page.locator('[name=name]').fill('Offline batch')
                page.locator('[name=start_date]').fill('2026-10-09')
                page.locator('[name=batch_size]').fill('5')
                page.locator('[name=initial_gravity]').fill('1.100')
                page.locator('[name=final_gravity]').fill('1.010')
                page.locator('main form button[type=submit]').click()
                page.wait_for_url('**/app/batches/**')
                page.goto(BASE + '/app/stats/')
                assert page.evaluate("() => !!Chart.getChart('abvChart')")
                expect(page.locator('#abvChart')).to_be_visible()
                page.goto(BASE + '/app/calendar')
                expect(page.locator('.fc-daygrid')).to_be_visible()
                page.locator('.fc-daygrid-day').first.click()
                expect(page.locator('#eventModal')).to_be_visible()
                page.locator('#event_title').fill('Offline event')
                page.locator('#event_start').fill('2026-10-09')
                page.locator('#eventForm').get_by_role('button', name='Save', exact=True).click()
                expect(page.locator('#eventModal')).to_be_hidden()
                expect(page.locator('.fc-event-title').filter(has_text='Offline event')).to_be_visible()
                assert not external, f'Unexpected remote browser dependencies: {external}'
                assert not errors, f'Browser JavaScript errors: {errors}'
                browser.close()
            print('Offline browser setup, login, rich-text/list round trip, ingredient removal, batch, chart and calendar checks passed.')
        except Exception:
            log.flush()
            print(log_path.read_text(), file=sys.stderr)
            raise
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    run()
