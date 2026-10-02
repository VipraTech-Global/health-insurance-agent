import base64
from copy import deepcopy

from apps.adviser_v2.demo.browser_sources import import_candidate
from apps.adviser_v2.demo.rejection_report import PARAPHRASE, paraphrase_only, summarize_rejections


def test_browser_viewer_html_is_not_a_pdf(tmp_path):
    row = {'insurer_id': 'icici', 'url': 'https://www.icicilombard.com/elevate.pdf',
           'source_url': 'https://www.icicilombard.com/downloads', 'label': 'Policy wordings',
           'status': 200, 'data': 'data:application/pdf;base64,' + base64.b64encode(b'<html>viewer</html>').decode()}
    result = import_candidate(row, tmp_path)
    assert result['status'] == 'unavailable'
    assert 'not PDF' in result['reason']
    assert not (tmp_path / 'objects').exists()


def test_official_pdf_cannot_be_imported_with_unverified_origin(tmp_path):
    result = import_candidate({'insurer_id': 'care', 'url': 'https://example.com/file.pdf',
        'source_url': 'https://www.careinsurance.com/other-downloads.html'}, tmp_path)
    assert result['status'] == 'unavailable'
    assert result['reason'] == 'Unverified official source host.'


def test_only_paraphrase_failures_are_counted_separately():
    check = {'checks': [True, True, True, False, True, True], 'problems': [PARAPHRASE], 'rejected_wrong_plan': 0}
    assert paraphrase_only(check)
    assert not paraphrase_only({**check, 'problems': [PARAPHRASE, 'Missing condition.']})
    assert not paraphrase_only({**check, 'rejected_wrong_plan': 1})
    assert not paraphrase_only({**check, 'checks': [True] * 6})
    assert not paraphrase_only(None)
    arm = {'status': 'not_found', 'validation': check, 'attempts': [{'validation': check}]}
    corrected = deepcopy(arm)
    corrected.update(status='answered', validation={'checks': [True]*6, 'problems': []})
    corrected['attempts'].append({'validation': corrected['validation']})
    rows = [{'job': {'kind': 'answer', 'id': 'case'}, 'arms': {'H': arm, 'P': corrected},
             'split_attempts': [{'H': arm, 'P': arm}]},
            {'job': {'kind': 'answer', 'id': 'unavailable'},
             'arms': {m: {'status': 'documents_unavailable'} for m in ('H', 'P')}}]
    report = summarize_rejections(rows)['arms']
    assert report['H']['answer_cases'] == report['P']['answer_cases'] == 2
    assert report['H']['final_unanswered_only_paraphrase'] == 1
    assert report['P']['final_unanswered_only_paraphrase'] == 0
    assert report['H']['paraphrase_only_attempts'] == report['P']['paraphrase_only_attempts'] == 1
    assert report['H']['split_pair_paraphrase_only_attempts'] == 1
    assert report['H']['case_ids'] == ['case']
