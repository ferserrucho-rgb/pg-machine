import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from collections import OrderedDict
from datetime import datetime, date, timedelta

# --- AUTH GATE (must be before any other UI) ---
from lib.auth import require_auth, get_current_user, is_admin, is_manager_or_admin, has_control_access, can_see_all_opportunities, logout, get_supabase, ALL_ROLES, ROLE_LABELS
from lib import dal
from lib import notifications

st.set_page_config(page_title="PG Machine", layout="wide", initial_sidebar_state="expanded")

if not require_auth():
    st.stop()

# --- Usuario autenticado ---
user = get_current_user()
team_id = user["team_id"]
user_id = user["id"]

# --- 1. ESTILOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    section.main > div[style] { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.5rem !important; }
    .cat-styled { color: white !important; font-weight: 800 !important; font-size: 0.8rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; border: none !important; border-radius: 6px !important; padding: 6px 10px !important; min-height: 0 !important; }
    .scorecard { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .badge { float:right; font-size:0.6rem; font-weight:bold; padding:2px 6px; border-radius:8px; text-transform: uppercase; border: 1.2px solid; }
    .sc-cuenta { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .sc-proyecto { color: #1e293b; font-size: 0.95rem; font-weight: 700; margin: 4px 0; }
    .sc-monto { color: #16a34a; font-size: 1.1rem; font-weight: 800; display: block; }
    .opp-meta-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px; margin-bottom: 10px; }
    .opp-meta-bar .meta-name { font-size: 0.85rem; font-weight: 800; color: #1e293b; }
    .opp-meta-bar .meta-cuenta { font-size: 0.7rem; font-weight: 600; color: #64748b; text-transform: uppercase; }
    .opp-meta-bar .meta-pill { font-size: 0.6rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
    .opp-meta-bar .meta-cat-leads { background: #dbeafe; color: #1d4ed8; }
    .opp-meta-bar .meta-cat-official { background: #d1fae5; color: #047857; }
    .opp-meta-bar .meta-cat-gtm { background: #fef3c7; color: #d97706; }
    .opp-meta-bar .meta-stage { background: #ede9fe; color: #7c3aed; }
    .opp-meta-bar .meta-monto { font-size: 0.8rem; font-weight: 800; color: #16a34a; }
    .opp-meta-bar .meta-id { font-family: 'Courier New', monospace; font-size: 0.55rem; font-weight: 700; color: #334155; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 1px 5px; border-radius: 3px; }
    .opp-meta-bar .meta-close { font-size: 0.6rem; font-weight: 700; color: #b91c1c; background: #fef2f2; border: 1px solid #fca5a5; padding: 1px 5px; border-radius: 3px; }
    .opp-meta-bar .meta-actions { margin-left: auto; display: flex; gap: 6px; flex-shrink: 0; }
    .meta-btn { cursor: pointer; font-size: 0.65rem; font-weight: 600; padding: 3px 8px; border-radius: 4px; transition: all 0.15s; }
    .meta-btn-back { color: #1a73e8; background: #eff6ff; }
    .meta-btn-back:hover { background: #1a73e8; color: white; }
    .meta-btn-del { color: #ef4444; background: #fef2f2; }
    .meta-btn-del:hover { background: #ef4444; color: white; }
    .meta-btn-edit-opp { color: #047857; background: #d1fae5; }
    .meta-btn-edit-opp:hover { background: #047857; color: white; }
    .meta-btn-new-act { color: #1a73e8; background: #eff6ff; }
    .meta-btn-new-act:hover { background: #1a73e8; color: white; }
    .action-panel { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 6px solid #1a73e8; }
    .hist-card { background: #f8fafc; padding: 10px 12px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 6px; border-left: 4px solid #94a3b8; font-size: 0.75rem; line-height: 1.4; }
    .act-top { display: flex; align-items: flex-start; gap: 8px; }
    .act-meta-row { flex: 1; display: flex; align-items: center; flex-wrap: wrap; gap: 5px; min-width: 0; }
    .act-actions { display: flex; gap: 3px; flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end; }
    .act-btn { cursor: pointer; font-size: 0.6rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; transition: all 0.15s; white-space: nowrap; }
    .act-btn-edit { color: #1a73e8; background: #eff6ff; }
    .act-btn-edit:hover { background: #1a73e8; color: white; }
    .act-btn-del { color: #ef4444; background: #fef2f2; }
    .act-btn-del:hover { background: #ef4444; color: white; }
    .act-btn-send { color: #047857; background: #d1fae5; }
    .act-btn-send:hover { background: #047857; color: white; }
    .act-btn-resp { color: #7c3aed; background: #ede9fe; }
    .act-btn-resp:hover { background: #7c3aed; color: white; }
    .act-btn-resend { color: #0369a1; background: #e0f2fe; }
    .act-btn-resend:hover { background: #0369a1; color: white; }
    .act-tipo { font-size: 0.65rem; font-weight: 700; color: white; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
    .act-tipo-email { background: #3b82f6; }
    .act-tipo-llamada { background: #f59e0b; }
    .act-tipo-reunion { background: #10b981; }
    .act-tipo-asignacion { background: #8b5cf6; }
    .act-obj { font-size: 0.72rem; font-weight: 700; color: #1e293b; }
    .act-dest { font-size: 0.62rem; font-weight: 600; color: #7c3aed; background: #ede9fe; padding: 1px 6px; border-radius: 8px; }
    .act-asig { font-size: 0.62rem; font-weight: 600; color: #0369a1; background: #e0f2fe; padding: 1px 6px; border-radius: 8px; }
    .act-fecha { font-size: 0.6rem; font-weight: 600; color: #94a3b8; }
    .act-estado { font-size: 0.62rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
    .act-desc { font-size: 0.68rem; color: #64748b; line-height: 1.4; margin-top: 3px; }
    .act-feedback { font-size: 0.68rem; color: #92400e; background: #fffbeb; border-left: 3px solid #f59e0b; padding: 3px 8px; margin-top: 4px; border-radius: 0 4px 4px 0; }
    .hist-card.tipo-email { border-left-color: #3b82f6; }
    .hist-card.tipo-llamada { border-left-color: #f59e0b; }
    .hist-card.tipo-reunion { border-left-color: #10b981; }
    .hist-card.tipo-asignacion { border-left-color: #8b5cf6; }
    .hist-card.enviada { background: #f5f3ff; border-left-color: #8b5cf6; }
    .hist-card.bloqueada { background: #fef2f2; border-left-color: #ef4444; }
    .hist-card.respondida { background: #f0fdf4; border-left-color: #16a34a; }
    .hist-card.pendiente { background: #fffbeb; border-left-color: #f59e0b; }
    .activity-line { font-size: 0.72rem; color: #475569; margin: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .account-group { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; margin-bottom: 8px; }
    .account-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .account-name { color: #1e293b; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
    .account-total { color: #16a34a; font-size: 0.7rem; font-weight: 800; }
    .account-badge { background: #e2e8f0; color: #475569; font-size: 0.65rem; font-weight: 600; padding: 2px 6px; border-radius: 6px; }
    /* Clickable card — whole card opens detail, × inside for delete */
    .pgm-card-wrap { position: relative; background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s; }
    .pgm-card-wrap:hover { border-color: #1a73e8; box-shadow: 0 3px 12px rgba(26,115,232,0.18); background: #f8faff; }
    .card-del-trigger { position: absolute; bottom: 6px; right: 8px; font-size: 0.75rem; color: #cbd5e1; cursor: pointer; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; border-radius: 50%; z-index: 5; transition: all 0.15s; }
    .card-del-trigger:hover { color: #ef4444; background: #fef2f2; }
    .bulk-del-bar { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 8px 14px; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    div[data-testid="stMultiSelect"] { margin-top: -8px !important; margin-bottom: -8px !important; }
    div[data-testid="stMultiSelect"] > div { min-height: 0 !important; }
    div[data-testid="stMultiSelect"] input { font-size: 0.7rem !important; }
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] { font-size: 0.65rem !important; height: 20px !important; }
    .pgm-card-wrap .opp-top { display: flex; justify-content: space-between; align-items: flex-start; }
    .pgm-card-wrap .opp-left { flex: 1; min-width: 0; }
    .pgm-card-wrap .opp-right { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; flex-shrink: 0; margin-left: 8px; }
    .pgm-card-wrap .opp-name { font-size: 0.85rem; font-weight: 700; color: #1e293b; line-height: 1.3; margin-bottom: 2px; }
    .pgm-card-wrap .opp-row2 { display: flex; align-items: center; gap: 8px; }
    .pgm-card-wrap .stage-badge { color: white; font-size: 0.58rem; font-weight: 600; font-style: normal; background: #8b5cf6; padding: 2px 7px; border-radius: 10px; font-family: Georgia, serif; letter-spacing: 0.03em; }
    .pgm-card-wrap .amount { color: #16a34a; font-size: 0.9rem; font-weight: 800; }
    .pgm-card-wrap .opp-id-box { font-family: 'Courier New', monospace; font-size: 0.55rem; font-weight: 700; color: #334155; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 1px 5px; border-radius: 3px; }
    .pgm-card-wrap .close-date { font-size: 0.6rem; font-weight: 700; color: #b91c1c; background: #fef2f2; border: 1px solid #fca5a5; padding: 1px 5px; border-radius: 3px; }
    .pgm-card-wrap .act-sep { border-top: 1px dashed #e2e8f0; margin: 6px 0 4px 0; }
    .pgm-card-wrap .act-line { font-size: 0.72rem; color: #334155; line-height: 1.5; padding: 3px 0 3px 8px; border-left: 3px solid #cbd5e1; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .pgm-card-wrap .act-line .act-obj { font-weight: 600; color: #1e293b; }
    .pgm-card-wrap .act-line .act-dest { color: #7c3aed; font-weight: 500; }
    .pgm-card-wrap .act-line .act-asig { color: #0369a1; font-weight: 600; font-size: 0.65rem; background: #e0f2fe; padding: 1px 4px; border-radius: 3px; }
    .pgm-card-wrap .act-line .act-status { font-weight: 600; font-size: 0.65rem; }
    /* User identity bar */
    .user-bar { background: #1e293b; color: white; padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .user-bar .user-avatar { background: #3b82f6; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; }
    .user-bar .user-role { background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; text-transform: uppercase; }
    /* Initials avatar badge */
    .avatar-badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #3b82f6; color: white; font-size: 0.6rem; font-weight: 700; margin: 0 2px; vertical-align: middle; }
    /* --- Mobile responsive --- */
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        section.main > div[style] { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        [data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; }
        button { min-height: 48px !important; font-size: 0.9rem !important; }
        input, select, textarea { font-size: 16px !important; }
        .pgm-card-wrap { padding: 8px 10px; }
        .pgm-card-wrap .opp-header { font-size: 0.8rem; }
        .pgm-card-wrap .amount { font-size: 0.85rem; }
        .account-group { padding: 5px 6px; margin-bottom: 6px; }
        .user-bar { font-size: 0.7rem; padding: 5px 10px; }
        .hist-card { padding: 10px; }
        .act-top { flex-direction: column; }
        .act-actions { justify-content: flex-start; }
        .cat-header { font-size: 0.85rem; padding: 8px; }
    }
    @media (max-width: 480px) {
        .pgm-card-wrap .opp-header { font-size: 0.75rem; }
        .pgm-card-wrap .amount { font-size: 0.8rem; }
        .pgm-card-wrap .act-line { font-size: 0.55rem; }
        .account-name { font-size: 0.75rem; }
        .account-total { font-size: 0.7rem; }
        .user-bar { font-size: 0.65rem; }
    }
    </style>
    """, unsafe_allow_html=True)

components.html("""
<script>
(function() {
    var doc = window.parent.document;
    if (doc._pgmObs) { try { doc._pgmObs.disconnect(); } catch(e){} }

    // Helper: walk up DOM from startEl, search subsequent siblings for button matching text
    function findBtn(startEl, textMatch) {
        var el = startEl;
        while (el && el !== doc.body) {
            var sib = el.nextElementSibling;
            while (sib) {
                var btns = sib.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if ((btns[i].textContent||'').indexOf(textMatch) >= 0) return btns[i];
                }
                sib = sib.nextElementSibling;
            }
            el = el.parentElement;
        }
        return null;
    }

    // Event delegation for all custom click handlers
    if (doc._pgmClickHandler) doc.body.removeEventListener('click', doc._pgmClickHandler);
    doc._pgmClickHandler = function(e) {
        // 1. Dashboard card click (open / delete)
        var card = e.target.closest('.pgm-card-wrap');
        if (card) {
            var el = card.parentElement;
            var btnRow = null;
            while (el) {
                var sib = el.nextElementSibling;
                if (sib) {
                    var hasOpen = false;
                    sib.querySelectorAll('button').forEach(function(b) {
                        if ((b.textContent||'').trim() === '\u25b8') hasOpen = true;
                    });
                    if (hasOpen) { btnRow = sib; break; }
                }
                el = el.parentElement;
            }
            if (!btnRow) return;
            if (e.target.closest('.card-del-trigger')) {
                btnRow.querySelectorAll('button').forEach(function(b) {
                    if ((b.textContent||'').trim() === '\u00d7') b.click();
                });
                return;
            }
            btnRow.querySelectorAll('button').forEach(function(b) {
                if ((b.textContent||'').trim() === '\u25b8') b.click();
            });
            return;
        }

        // 2. Meta-bar back button
        if (e.target.closest('.meta-btn-back')) {
            var bar = e.target.closest('.opp-meta-bar');
            if (bar) { var b = findBtn(bar, 'Volver'); if (b) b.click(); }
            return;
        }

        // 3. Meta-bar delete button
        if (e.target.closest('.meta-btn-del')) {
            var bar = e.target.closest('.opp-meta-bar');
            if (bar) { var b = findBtn(bar, 'Eliminar'); if (b) b.click(); }
            return;
        }

        // 4. Meta-bar edit opportunity
        if (e.target.closest('.meta-btn-edit-opp')) {
            var bar = e.target.closest('.opp-meta-bar');
            if (bar) { var b = findBtn(bar, 'EDIT_OPP'); if (b) b.click(); }
            return;
        }

        // 5. Meta-bar new activity
        if (e.target.closest('.meta-btn-new-act')) {
            var bar = e.target.closest('.opp-meta-bar');
            if (bar) { var b = findBtn(bar, 'NEW_ACT'); if (b) b.click(); }
            return;
        }

        // 6. Activity edit button
        if (e.target.closest('.act-btn-edit')) {
            var hc = e.target.closest('.hist-card');
            if (hc) { var b = findBtn(hc, 'Editar'); if (b) b.click(); }
            return;
        }

        // 5. Activity delete button
        if (e.target.closest('.act-btn-del')) {
            var hc = e.target.closest('.hist-card');
            if (hc) { var b = findBtn(hc, '\u232b'); if (b) b.click(); }
            return;
        }

        // 6. Activity send (mark as Enviada)
        if (e.target.closest('.act-btn-send')) {
            var hc = e.target.closest('.hist-card');
            if (hc) { var b = findBtn(hc, 'ENVIADO'); if (b) b.click(); }
            return;
        }

        // 7. Activity responded
        if (e.target.closest('.act-btn-resp')) {
            var hc = e.target.closest('.hist-card');
            if (hc) { var b = findBtn(hc, 'RESPONDIDA'); if (b) b.click(); }
            return;
        }

        // 8. Activity resend
        if (e.target.closest('.act-btn-resend')) {
            var hc = e.target.closest('.hist-card');
            if (hc) { var b = findBtn(hc, 'REENVIAR'); if (b) b.click(); }
            return;
        }
    };
    doc.body.addEventListener('click', doc._pgmClickHandler);

    function pgmFix() {
        // Full-width layout
        doc.querySelectorAll('section.main > div').forEach(function(el) {
            if (el.style.maxWidth) { el.style.maxWidth='100%'; el.style.paddingLeft='1rem'; el.style.paddingRight='1rem'; }
        });
        // Style category buttons with colored gradients
        doc.querySelectorAll('button').forEach(function(btn) {
            var txt = (btn.textContent||'').trim().toUpperCase();
            var grad = null;
            if (txt === 'LEADS' || (txt.indexOf('LEADS')>=0 && txt.indexOf('\u2715')>=0)) grad = 'linear-gradient(135deg,#3b82f6,#1d4ed8)';
            else if (txt === 'OFFICIAL' || (txt.indexOf('OFFICIAL')>=0 && txt.indexOf('\u2715')>=0)) grad = 'linear-gradient(135deg,#10b981,#047857)';
            else if (txt === 'GTM' || (txt.indexOf('GTM')>=0 && txt.indexOf('\u2715')>=0)) grad = 'linear-gradient(135deg,#f59e0b,#d97706)';
            if (grad && !btn.dataset.catStyled) {
                btn.dataset.catStyled = '1';
                btn.style.background = grad;
                btn.style.color = 'white';
                btn.style.fontWeight = '800';
                btn.style.fontSize = '0.8rem';
                btn.style.letterSpacing = '0.05em';
                btn.style.textTransform = 'uppercase';
                btn.style.border = 'none';
                btn.style.borderRadius = '6px';
                btn.style.minHeight = '0';
                if (txt.indexOf('\u2715')>=0) btn.style.opacity = '0.75';
            }
        });
        // Hide button rows below dashboard cards
        doc.querySelectorAll('.pgm-card-wrap').forEach(function(card) {
            var el = card.parentElement;
            while (el) {
                var sib = el.nextElementSibling;
                if (sib) {
                    var hasCardBtn = false;
                    sib.querySelectorAll('button').forEach(function(b) {
                        var t = (b.textContent||'').trim();
                        if (t === '\u25b8' || t === '\u00d7') hasCardBtn = true;
                    });
                    if (hasCardBtn) {
                        sib.style.cssText = 'position:absolute !important;left:-9999px !important;height:0 !important;overflow:hidden !important;';
                        break;
                    }
                }
                el = el.parentElement;
            }
        });
        // Hide Volver/Eliminar row in detail view (replaced by meta-bar buttons)
        doc.querySelectorAll('button').forEach(function(btn) {
            var txt = (btn.textContent||'').trim();
            if (txt.indexOf('Volver') >= 0 && txt.indexOf('\u2b05') >= 0) {
                var el = btn;
                while (el && el !== doc.body) {
                    if (el.previousElementSibling && el.previousElementSibling.querySelector && el.previousElementSibling.querySelector('.opp-meta-bar')) {
                        el.style.cssText = 'position:absolute !important;left:-9999px !important;height:0 !important;overflow:hidden !important;';
                        break;
                    }
                    el = el.parentElement;
                }
            }
        });
        // Hide activity Streamlit buttons (replaced by in-card pill buttons)
        doc.querySelectorAll('button').forEach(function(btn) {
            var txt = (btn.textContent||'').trim();
            var hide = false;
            if (txt.indexOf('Editar') >= 0 && txt.indexOf('Oportunidad') < 0 && !btn.closest('form')) hide = true;
            if (txt.indexOf('\u232b') >= 0) hide = true;
            if (txt.indexOf('ENVIADO') >= 0) hide = true;
            if (txt.indexOf('RESPONDIDA') >= 0) hide = true;
            if (txt.indexOf('REENVIAR') >= 0) hide = true;
            if (txt.indexOf('EDIT_OPP') >= 0) hide = true;
            if (txt.indexOf('NEW_ACT') >= 0) hide = true;
            if (hide) {
                // Walk up hiding single-child wrappers until parent has other visible content
                var el = btn;
                while (el && el !== doc.body) {
                    el.style.cssText = 'display:none !important;';
                    var par = el.parentElement;
                    if (!par) break;
                    var anyVisible = false;
                    for (var i = 0; i < par.children.length; i++) {
                        if (par.children[i] !== el && par.children[i].style.cssText.indexOf('display:none') < 0 && par.children[i].style.cssText.indexOf('display: none') < 0) {
                            anyVisible = true; break;
                        }
                    }
                    if (anyVisible) break;
                    el = par;
                }
            }
        });
    }

    doc._pgmObs = new MutationObserver(pgmFix);
    doc._pgmObs.observe(doc.body, {childList: true, subtree: true});
    pgmFix();

    if (window.parent.innerWidth <= 768) {
        var params = new URLSearchParams(window.parent.location.search);
        if (!params.has('_mob')) {
            params.set('_mob', '1');
            window.parent.history.replaceState({}, '', '?' + params.toString());
        }
    }
})();
</script>
""", height=0)

is_mobile = st.query_params.get("_mob") == "1"

def _get_initials(full_name: str) -> str:
    """Extrae iniciales: primera letra del nombre + primera del apellido."""
    parts = (full_name or "").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif parts:
        return parts[0][:2].upper()
    return "??"

user_initials = _get_initials(user["full_name"])
user_role_label = ROLE_LABELS.get(user["role"], user["role"])
user_bar_html = f'<div class="user-bar"><span class="user-avatar">{user_initials}</span> {user["full_name"]} <span class="user-role">{user_role_label}</span></div>'

# --- 2. DATOS DESDE SUPABASE ---
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None
if 'focused_cat' not in st.session_state:
    st.session_state.focused_cat = None

# Cargar configuración del equipo
SLA_OPCIONES = dal.get_sla_options(team_id)
SLA_RESPUESTA = dal.get_sla_respuesta(team_id)
CATEGORIAS = dal.get_categorias(team_id)

# Cargar miembros del equipo para asignaciones
team_members = dal.get_team_members(team_id)
RECURSOS_PRESALES = {m["id"]: f'{m["full_name"]} ({m["specialty"]})' if m.get("specialty") else m["full_name"] for m in team_members}

def _parse_date(val):
    if not val or str(val).strip() in ("", "NaT", "nan", "None"):
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def _sla_to_hours(sla_key: str) -> int | None:
    """Convierte clave SLA a horas totales."""
    cfg = SLA_OPCIONES.get(sla_key, {})
    if "horas" in cfg:
        return cfg["horas"]
    if "dias" in cfg:
        return cfg["dias"] * 24
    return None

def _naive(dt):
    """Strip timezone info to make datetime naive (for safe arithmetic)."""
    if dt and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def _traffic_light(act):
    """Calcula semáforo para una actividad (formato Supabase)."""
    estado = act.get("estado", "Pendiente")
    now = datetime.now()

    if estado == "Respondida":
        return "🟩", "Respondida"

    if estado == "Enviada":
        enviada_ts = _naive(datetime.fromisoformat(act["enviada_ts"])) if act.get("enviada_ts") else now
        sla_dias = act.get("sla_respuesta_dias", 7)
        deadline = enviada_ts + timedelta(days=sla_dias)
        remaining = deadline - now
        if remaining.total_seconds() <= 0:
            return "🟥", "Bloqueada"
        return "🟪", f"Esp. rpta {remaining.days}d"

    # Pendiente
    fecha_str = act.get("fecha", "")
    if isinstance(fecha_str, date):
        fecha = fecha_str
    else:
        fecha = _parse_date(fecha_str) or date.today()

    hoy = date.today()
    if fecha > hoy:
        return "🟨", f"Pendiente {fecha.strftime('%d/%m')}"
    if fecha == hoy:
        return "🟨", "Hoy"

    # SLA check
    sla_deadline_str = act.get("sla_deadline")
    if sla_deadline_str:
        deadline = _naive(datetime.fromisoformat(sla_deadline_str)) if isinstance(sla_deadline_str, str) else _naive(sla_deadline_str)
        created = _naive(datetime.fromisoformat(act["created_at"])) if isinstance(act.get("created_at"), str) else (_naive(act.get("created_at")) or now)
        remaining = deadline - now
        if remaining.total_seconds() <= 0:
            return "🟥", "Vencida"
        total = deadline - created
        ratio = remaining / total if total.total_seconds() > 0 else 0
        hours_left = remaining.total_seconds() / 3600
        if ratio > 0.5:
            return ("🟩", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟩", f"{remaining.days}d rest.")
        return ("🟨", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟨", f"{remaining.days}d rest.")

    # Fallback from sla_key
    sla_cfg = SLA_OPCIONES.get(act.get("sla_key", ""), {})
    created = _naive(datetime.fromisoformat(act["created_at"])) if act.get("created_at") else now
    if "horas" in sla_cfg:
        deadline = created + timedelta(hours=sla_cfg["horas"])
    else:
        deadline = created + timedelta(days=sla_cfg.get("dias", 7))
    remaining = deadline - now
    if remaining.total_seconds() <= 0:
        return "🟥", "Vencida"
    total = deadline - created
    ratio = remaining / total if total.total_seconds() > 0 else 0
    hours_left = remaining.total_seconds() / 3600
    if ratio > 0.5:
        return ("🟩", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟩", f"{remaining.days}d rest.")
    return ("🟨", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟨", f"{remaining.days}d rest.")


# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🚀 PG Machine")
    st.caption(f"👤 {user['full_name']} ({user_role_label})")
    if st.button("Cerrar Sesión", key="logout_btn"):
        logout()

    st.divider()

    with st.expander("📥 CARGA MASIVA (EXCEL)", expanded=True):
        perfil = st.radio("Formato:", ["Leads Propios", "Forecast BMC"])
        up = st.file_uploader("Subir Archivo", type=["xlsx"])

        # Paso 1: Analizar archivo
        if up and st.button("Analizar Archivo"):
            df = pd.read_excel(up)
            items = []
            for _, r in df.iterrows():
                if perfil == "Leads Propios":
                    parsed = _parse_date(r.get('Close Date', None))
                    items.append({
                        "proyecto": str(r.get('Proyecto', 'S/N')),
                        "cuenta": str(r.get('Empresa', r.get('Cuenta', 'S/N'))),
                        "monto": float(r.get('Valor', r.get('Monto', 0)) or 0),
                        "categoria": "LEADS",
                        "close_date": str(parsed) if parsed else None,
                    })
                else:
                    parsed = _parse_date(r.get('Close Date', None))
                    items.append({
                        "proyecto": str(r.get('Opportunity Name', '-')),
                        "cuenta": str(r.get('Account Name', '-')),
                        "monto": float(r.get('Amount USD', 0) or 0),
                        "categoria": "OFFICIAL",
                        "opp_id": str(r.get('BMC Opportunity Id', '')),
                        "stage": str(r.get('Stage', '')),
                        "close_date": str(parsed) if parsed else None,
                    })

            # Comparar con existentes
            existing = dal.get_opportunities(team_id)
            # Índices de búsqueda
            by_opp_id = {o["opp_id"]: o for o in existing if o.get("opp_id")}
            by_proy_cuenta = {(o["proyecto"], o["cuenta"]): o for o in existing}

            nuevas = []
            iguales = []
            con_cambios = []  # (item_excel, opp_existente, campos_dif)
            compare_fields = ["proyecto", "cuenta", "monto", "categoria", "opp_id", "stage", "close_date"]

            for item in items:
                match = None
                # Match por opp_id primero (Forecast BMC)
                if item.get("opp_id") and item["opp_id"] in by_opp_id:
                    match = by_opp_id[item["opp_id"]]
                # Luego por proyecto + cuenta
                elif (item["proyecto"], item["cuenta"]) in by_proy_cuenta:
                    match = by_proy_cuenta[(item["proyecto"], item["cuenta"])]

                if match:
                    diffs = {}
                    for f in compare_fields:
                        val_new = str(item.get(f, "") or "")
                        val_old = str(match.get(f, "") or "")
                        if val_new != val_old and val_new:
                            diffs[f] = {"excel": item.get(f), "actual": match.get(f)}
                    if diffs:
                        con_cambios.append((item, match, diffs))
                    else:
                        iguales.append(item)
                else:
                    nuevas.append(item)

            st.session_state["import_nuevas"] = nuevas
            st.session_state["import_iguales"] = iguales
            st.session_state["import_con_cambios"] = con_cambios
            st.session_state["import_analizado"] = True

        # Paso 2: Mostrar resultados y opciones
        if st.session_state.get("import_analizado"):
            nuevas = st.session_state.get("import_nuevas", [])
            iguales = st.session_state.get("import_iguales", [])
            con_cambios = st.session_state.get("import_con_cambios", [])

            st.markdown(f"**Resultado del análisis:**")
            st.markdown(f"- 🆕 **{len(nuevas)}** nuevas")
            st.markdown(f"- ✅ **{len(iguales)}** sin cambios (se omiten)")
            st.markdown(f"- ⚠️ **{len(con_cambios)}** con diferencias")

            # Nuevas: checkbox individual para aceptar/rechazar
            if nuevas:
                st.markdown("---")
                st.markdown("**🆕 Nuevas oportunidades:**")
                nc1, nc2 = st.columns([0.8, 0.2])
                select_all_new = nc2.checkbox("Todas", value=True, key="sel_all_new")
                for i, item in enumerate(nuevas):
                    monto_str = f"USD {float(item.get('monto', 0)):,.0f}"
                    st.checkbox(
                        f"{item['cuenta']} — {item['proyecto']} ({monto_str})",
                        value=select_all_new,
                        key=f"imp_new_{i}",
                    )

            # Con cambios: checkbox individual + detalle de diffs
            if con_cambios:
                st.markdown("---")
                st.markdown("**⚠️ Con diferencias (sobrescribir con Excel):**")
                cc1, cc2 = st.columns([0.8, 0.2])
                select_all_chg = cc2.checkbox("Todas", value=False, key="sel_all_chg")
                for i, (item, existing_opp, diffs) in enumerate(con_cambios):
                    diff_summary = ", ".join(f"{f}: {v['actual']} → {v['excel']}" for f, v in diffs.items())
                    st.checkbox(
                        f"{item['cuenta']} — {item['proyecto']}",
                        value=select_all_chg,
                        key=f"imp_chg_{i}",
                        help=diff_summary,
                    )

            st.markdown("---")
            bc1, bc2 = st.columns(2)
            if bc1.button("Ejecutar Importación", key="exec_import", use_container_width=True):
                created = 0
                updated = 0
                skipped_new = 0
                # Crear nuevas seleccionadas
                selected_nuevas = [item for i, item in enumerate(nuevas) if st.session_state.get(f"imp_new_{i}")]
                skipped_new = len(nuevas) - len(selected_nuevas)
                if selected_nuevas:
                    created = dal.bulk_create_opportunities(team_id, user_id, selected_nuevas)
                # Actualizar cambios seleccionados
                for i, (item, existing_opp, diffs) in enumerate(con_cambios):
                    if st.session_state.get(f"imp_chg_{i}"):
                        update_data = {f: item[f] for f in diffs}
                        dal.update_opportunity(existing_opp["id"], update_data)
                        updated += 1

                parts = []
                if created:
                    parts.append(f"{created} creadas")
                if updated:
                    parts.append(f"{updated} actualizadas")
                if iguales:
                    parts.append(f"{len(iguales)} sin cambios")
                if skipped_new:
                    parts.append(f"{skipped_new} omitidas")
                st.success(f"Importación completada: {', '.join(parts)}")

                # Limpiar estado
                keys_to_clear = ["import_nuevas", "import_iguales", "import_con_cambios", "import_analizado"]
                keys_to_clear += [f"imp_new_{i}" for i in range(len(nuevas))]
                keys_to_clear += [f"imp_chg_{i}" for i in range(len(con_cambios))]
                keys_to_clear += ["sel_all_new", "sel_all_chg"]
                for k in keys_to_clear:
                    st.session_state.pop(k, None)
                st.rerun()

            if bc2.button("Cancelar", key="cancel_import", use_container_width=True):
                keys_to_clear = ["import_nuevas", "import_iguales", "import_con_cambios", "import_analizado"]
                keys_to_clear += [f"imp_new_{i}" for i in range(len(nuevas))]
                keys_to_clear += [f"imp_chg_{i}" for i in range(len(con_cambios))]
                keys_to_clear += ["sel_all_new", "sel_all_chg"]
                for k in keys_to_clear:
                    st.session_state.pop(k, None)
                st.rerun()

    st.divider()
    st.write("✍️ **ALTA MANUAL**")
    with st.form("manual_entry"):
        nc = st.text_input("Cuenta")
        np = st.text_input("Proyecto")
        nm = st.number_input("Monto USD", value=0)
        ncat = st.selectbox("Categoría", CATEGORIAS)
        n_opp_id = st.text_input("Opportunity ID")
        n_stage = st.text_input("Stage")
        n_close = st.date_input("Close Date", value=None)
        if st.form_submit_button("Añadir Individual"):
            if nc and np:
                parsed = _parse_date(n_close)
                dal.create_opportunity(team_id, user_id, {
                    "proyecto": np, "cuenta": nc, "monto": nm,
                    "categoria": ncat, "opp_id": n_opp_id,
                    "stage": n_stage,
                    "close_date": str(parsed) if parsed else None,
                })
                st.rerun()


# --- 4. LAYOUT ---
if st.session_state.selected_id:
    # --- VISTA DETALLE ---
    st.markdown(user_bar_html, unsafe_allow_html=True)
    opp = dal.get_opportunity(st.session_state.selected_id)
    if not opp:
        st.error("Oportunidad no encontrada.")
        st.session_state.selected_id = None
        st.rerun()

    # --- Opportunity metadata bar (single line) ---
    monto_val = float(opp.get("monto") or 0)
    cat_upper = opp["categoria"].strip().upper()
    cat_cls = "meta-cat-leads" if "LEAD" in cat_upper else ("meta-cat-official" if "OFFICIAL" in cat_upper else "meta-cat-gtm")
    meta_parts = [
        f'<span class="meta-name">{opp["proyecto"]}</span>',
        f'<span class="meta-cuenta">{opp["cuenta"]}</span>',
        f'<span class="meta-pill {cat_cls}">{opp["categoria"]}</span>',
    ]
    if opp.get("stage"):
        meta_parts.append(f'<span class="meta-pill meta-stage">{opp["stage"]}</span>')
    meta_parts.append(f'<span class="meta-monto">USD {monto_val:,.0f}</span>')
    if opp.get("opp_id"):
        meta_parts.append(f'<span class="meta-id">{opp["opp_id"]}</span>')
    if opp.get("close_date"):
        meta_parts.append(f'<span class="meta-close">Cierre: {opp["close_date"]}</span>')
    action_html = '<span class="meta-actions"><span class="meta-btn meta-btn-edit-opp">✏ Editar</span><span class="meta-btn meta-btn-new-act">+ Nueva</span><span class="meta-btn meta-btn-back">⬅ Volver</span><span class="meta-btn meta-btn-del">🗑 Eliminar</span></span>'
    st.markdown(f'<div class="opp-meta-bar">{"".join(meta_parts)}{action_html}</div>', unsafe_allow_html=True)

    # --- Hidden action buttons (wired via JS) ---
    _hid_c1, _hid_c2 = st.columns(2)
    if _hid_c1.button("⬅️ Volver", use_container_width=True, key="detail_back"):
        st.session_state.selected_id = None
        st.rerun()
    if _hid_c2.button("🗑️ Eliminar", key="del_opp", use_container_width=True):
        st.session_state[f"confirm_del_opp_{opp['id']}"] = True
    if st.session_state.get(f"confirm_del_opp_{opp['id']}"):
        st.warning(f"Eliminar **{opp['proyecto']}** y todas sus actividades?")
        dc1, dc2 = st.columns(2)
        if dc1.button("Confirmar", key="confirm_del_opp_yes", use_container_width=True):
            dal.delete_opportunity(opp["id"])
            st.session_state.selected_id = None
            st.session_state.pop(f"confirm_del_opp_{opp['id']}", None)
            st.rerun()
        if dc2.button("Cancelar", key="confirm_del_opp_no", use_container_width=True):
            st.session_state.pop(f"confirm_del_opp_{opp['id']}", None)
            st.rerun()

    # Hidden toggles for edit opp / new activity (wired via JS)
    if st.button("✏ EDIT_OPP", key="toggle_edit_opp"):
        st.session_state["show_edit_opp"] = not st.session_state.get("show_edit_opp", False)
        st.rerun()
    if st.button("+ NEW_ACT", key="toggle_new_act"):
        st.session_state["show_new_act"] = not st.session_state.get("show_new_act", False)
        st.rerun()

    # --- History ---
    st.caption("📜 Historial e Interacción")
    activities = dal.get_activities_for_opportunity(opp["id"])
    _estado_order = {"Bloqueada": 0, "Pendiente": 1, "Enviada": 2, "Respondida": 3}
    def _act_sort_key(a):
        e = a.get("estado", "")
        if e == "Enviada":
            light, lbl = _traffic_light(a)
            if lbl == "Bloqueada":
                return 0
        return _estado_order.get(e, 2)
    activities.sort(key=_act_sort_key)
    for a in activities:
        with st.container():
            dest_txt = f' → {a["destinatario"]}' if a.get("destinatario") else ""
            assigned_name = ""
            if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                assigned_name = a["assigned_profile"]["full_name"]
            elif a.get("assigned_to"):
                assigned_name = RECURSOS_PRESALES.get(a["assigned_to"], "")
            # For Email/Llamada/Reunión, show creator as the person performing the action
            if not assigned_name and a.get("tipo") in ("Email", "Llamada", "Reunión"):
                if a.get("creator_profile") and a["creator_profile"].get("full_name"):
                    assigned_name = a["creator_profile"]["full_name"]

            light, label = _traffic_light(a)
            tipo_lower = a.get("tipo", "").lower().replace("ó", "o")
            tipo_class = f'tipo-{tipo_lower}' if a.get("tipo") else ""
            if a["estado"] == "Enviada" and label == "Bloqueada":
                card_class = "hist-card bloqueada"
                estado_pill = '<span class="act-estado" style="color:#ef4444;background:#fef2f2;">🟥 BLOQUEADA</span>'
            elif a["estado"] == "Enviada":
                card_class = "hist-card enviada"
                estado_pill = f'<span class="act-estado" style="color:#7c3aed;background:#ede9fe;">🟪 Enviada — {label}</span>'
            elif a["estado"] == "Respondida":
                card_class = "hist-card respondida"
                estado_pill = '<span class="act-estado" style="color:#047857;background:#d1fae5;">🟩 Respondida</span>'
            elif a["estado"] == "Pendiente":
                card_class = "hist-card pendiente"
                estado_pill = '<span class="act-estado" style="color:#d97706;background:#fef3c7;">🟨 Pendiente</span>'
            else:
                card_class = f"hist-card {tipo_class}"
                estado_pill = f'<span class="act-estado" style="color:#64748b;background:#f1f5f9;">{a["estado"]}</span>'

            asig_initials = _get_initials(assigned_name) if assigned_name else ""
            fecha_display = str(a.get("fecha", ""))
            tipo_icons = {"Email": "📧", "Llamada": "📞", "Reunión": "🤝", "Asignación": "👤"}
            tipo_icon = tipo_icons.get(a.get("tipo", ""), "📋")
            tipo_cls = f'act-tipo-{tipo_lower}' if tipo_lower else ''

            # Metadata elements
            tipo_html = f'<span class="act-tipo {tipo_cls}">{tipo_icon} {a["tipo"]}</span>'
            obj_html = f'<span class="act-obj">{a["objetivo"]}</span>' if a.get("objetivo") else ''
            dest_html = f'<span class="act-dest">→ {a["destinatario"]}</span>' if a.get("destinatario") else ''
            asig_html = f'<span class="act-asig"><span class="avatar-badge" style="width:16px;height:16px;font-size:0.5rem;">{asig_initials}</span> {assigned_name}</span>' if assigned_name else ''
            fecha_html = f'<span class="act-fecha">{fecha_display}</span>'
            desc_html = f'<div class="act-desc">{a.get("descripcion", "")}</div>' if a.get("descripcion") else ''
            fb_html = f'<div class="act-feedback"><b>Feedback:</b> {a["feedback"]}</div>' if a.get("feedback") else ''

            # Action buttons
            estado_btns = ''
            if a["estado"] == "Pendiente":
                estado_btns = '<span class="act-btn act-btn-send">✅ Enviado</span>'
            elif a["estado"] == "Enviada":
                estado_btns = '<span class="act-btn act-btn-resp">📩 Respondida</span><span class="act-btn act-btn-resend">🔄 Reenviar</span>'
            act_btns = f'<span class="act-actions">{estado_btns}<span class="act-btn act-btn-edit">✏ Editar</span><span class="act-btn act-btn-del">🗑 Eliminar</span></span>'

            # Build meta-row: Asignación shows assignee first → destinatario
            if a.get("tipo") == "Asignación":
                meta_row = f'{tipo_html}{asig_html}{dest_html}{obj_html}{estado_pill}{fecha_html}'
            else:
                meta_row = f'{tipo_html}{obj_html}{dest_html}{asig_html}{estado_pill}{fecha_html}'

            st.markdown(f'<div class="{card_class}"><div class="act-top"><div class="act-meta-row">{meta_row}</div>{act_btns}</div>{desc_html}{fb_html}</div>', unsafe_allow_html=True)

            aid = a['id']
            # State-specific action buttons
            if a["estado"] == "Pendiente":
                if st.button("✅ ENVIADO", key=f"d_{aid}", use_container_width=True):
                    dal.update_activity(aid, {"estado": "Enviada"})
                    st.rerun()
            elif a["estado"] == "Enviada":
                if st.session_state.get(f"show_fb_{aid}"):
                    with st.form(f"fb_form_{aid}"):
                        feedback = st.text_area("Feedback del cliente")
                        st.divider()
                        crear_seguimiento = st.checkbox("🔁 Crear actividad de seguimiento", value=False, key=f"seg_{aid}")
                        seg_fecha = st.date_input("Fecha seguimiento", value=date.today() + timedelta(days=7), key=f"segf_{aid}")
                        if st.form_submit_button("Confirmar Respuesta"):
                            dal.update_activity(aid, {"estado": "Respondida", "feedback": feedback})
                            if crear_seguimiento:
                                dal.create_activity(a["opportunity_id"], a["team_id"], user_id, {
                                    "tipo": a.get("tipo", "Email"),
                                    "fecha": str(seg_fecha),
                                    "objetivo": a.get("objetivo", ""),
                                    "descripcion": f'Seguimiento: {feedback}' if feedback else a.get("descripcion", ""),
                                    "sla_key": a.get("sla_key", ""),
                                    "sla_hours": a.get("sla_hours"),
                                    "sla_respuesta_dias": a.get("sla_respuesta_dias", 7),
                                    "destinatario": a.get("destinatario", ""),
                                    "assigned_to": a.get("assigned_to"),
                                })
                            st.session_state.pop(f"show_fb_{aid}", None)
                            st.rerun()
                else:
                    b1, b2 = st.columns(2)
                    if b1.button("📩 RESPONDIDA", key=f"r_{aid}", use_container_width=True):
                        st.session_state[f"show_fb_{aid}"] = True
                        st.rerun()
                    if b2.button("🔄 REENVIAR", key=f"re_{aid}", use_container_width=True):
                        dal.update_activity(aid, {"estado": "Pendiente", "enviada_ts": None, "response_deadline": None})
                        st.rerun()

            # Hidden edit/delete triggers (wired via JS from in-card buttons)
            if st.button("✏️ Editar", key=f"toggle_edit_{aid}"):
                st.session_state[f"show_edit_{aid}"] = not st.session_state.get(f"show_edit_{aid}", False)
                st.rerun()
            if st.button("⌫", key=f"act_del_{aid}"):
                st.session_state[f"confirm_del_act_{aid}"] = True

            # Delete confirmation
            if st.session_state.get(f"confirm_del_act_{aid}"):
                st.warning("Eliminar esta actividad?")
                da1, da2 = st.columns(2)
                if da1.button("Confirmar", key=f"cdel_act_y_{aid}", use_container_width=True):
                    dal.delete_activity(aid)
                    st.session_state.pop(f"confirm_del_act_{aid}", None)
                    st.rerun()
                if da2.button("Cancelar", key=f"cdel_act_n_{aid}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_act_{aid}", None)
                    st.rerun()

            # Inline edit form (toggled)
            if st.session_state.get(f"show_edit_{aid}"):
                with st.form(f"edit_act_{aid}"):
                    ea_c1, ea_c2, ea_c3 = st.columns(3)
                    ea_tipo = ea_c1.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"],
                        index=["Email", "Llamada", "Reunión", "Asignación"].index(a.get("tipo", "Email")) if a.get("tipo", "Email") in ["Email", "Llamada", "Reunión", "Asignación"] else 0,
                        key=f"et_{aid}")
                    sla_keys = list(SLA_OPCIONES.keys())
                    ea_sla = ea_c2.selectbox("SLA", sla_keys,
                        index=sla_keys.index(a["sla_key"]) if a.get("sla_key") in sla_keys else 0,
                        key=f"es_{aid}")
                    ea_fecha = ea_c3.date_input("Fecha", value=_parse_date(a.get("fecha", "")) or date.today(), key=f"ef_{aid}")
                    ea_c4, ea_c5 = st.columns(2)
                    ea_objetivo = ea_c4.text_input("Objetivo", value=a.get("objetivo", ""), key=f"eo_{aid}")
                    ea_dest = ea_c5.text_input("Destinatario", value=a.get("destinatario", ""), key=f"ed_{aid}")
                    sla_rpta_keys = list(SLA_RESPUESTA.keys())
                    sla_rpta_vals = list(SLA_RESPUESTA.values())
                    cur_sla_idx = sla_rpta_vals.index(a.get("sla_respuesta_dias", 7)) if a.get("sla_respuesta_dias", 7) in sla_rpta_vals else 1
                    ea_sla_rpta = st.selectbox("SLA Respuesta", sla_rpta_keys, index=cur_sla_idx, key=f"esr_{aid}")
                    ea_desc = st.text_area("Descripción", value=a.get("descripcion", ""), height=60, key=f"edc_{aid}")
                    fc1, fc2 = st.columns(2)
                    if fc1.form_submit_button("💾 Guardar"):
                        new_sla_hours = _sla_to_hours(ea_sla)
                        dal.update_activity(aid, {
                            "tipo": ea_tipo, "sla_key": ea_sla, "sla_hours": new_sla_hours,
                            "fecha": str(ea_fecha), "objetivo": ea_objetivo,
                            "destinatario": ea_dest, "sla_respuesta_dias": SLA_RESPUESTA[ea_sla_rpta],
                            "descripcion": ea_desc,
                        })
                        st.session_state.pop(f"show_edit_{aid}", None)
                        st.rerun()

    if not activities:
        st.info("No hay actividades registradas aún.")

    # --- Edit Opportunity (toggled from meta-bar) ---
    if st.session_state.get("show_edit_opp"):
        st.caption("✏️ Editar Oportunidad")
        with st.form("edit_opp"):
            ed_c1, ed_c2, ed_c3 = st.columns(3)
            ed_cuenta = ed_c1.text_input("Cuenta", value=opp["cuenta"])
            ed_proyecto = ed_c2.text_input("Proyecto", value=opp["proyecto"])
            ed_monto = ed_c3.number_input("Monto USD", value=float(opp.get("monto") or 0))
            ed_c4, ed_c5, ed_c6 = st.columns(3)
            ed_cat = ed_c4.selectbox("Categoría", CATEGORIAS, index=CATEGORIAS.index(opp["categoria"]) if opp["categoria"] in CATEGORIAS else 0)
            ed_opp_id = ed_c5.text_input("Opportunity ID", value=opp.get("opp_id", ""))
            ed_stage = ed_c6.text_input("Stage", value=opp.get("stage", ""))
            close_val = _parse_date(opp.get("close_date", ""))
            ed_close = st.date_input("Close Date", value=close_val)
            if st.form_submit_button("💾 Guardar Cambios"):
                dal.update_opportunity(opp["id"], {
                    "cuenta": ed_cuenta, "proyecto": ed_proyecto,
                    "monto": float(ed_monto), "categoria": ed_cat,
                    "opp_id": ed_opp_id, "stage": ed_stage,
                    "close_date": str(ed_close) if ed_close else None,
                })
                st.session_state.pop("show_edit_opp", None)
                st.rerun()

    # --- New Activity (toggled from meta-bar) ---
    if st.session_state.get("show_new_act"):
        st.caption("➕ Nueva Actividad")
        tipo = st.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"])
        with st.form("act_form"):
            c1, c2, c3 = st.columns(3)
            sla_key = c1.selectbox("SLA", list(SLA_OPCIONES.keys()))
            fecha = c2.date_input("Fecha", value=date.today())
            objetivo = c3.text_input("Objetivo")
            asignado_a_id = None
            if tipo == "Asignación":
                c4, c5, c6 = st.columns(3)
                destinatario = c4.text_input("Destinatario")
                recurso_opciones = [""] + list(RECURSOS_PRESALES.values())
                recurso_ids = [""] + list(RECURSOS_PRESALES.keys())
                sel_idx = c5.selectbox("Asignado a", range(len(recurso_opciones)), format_func=lambda i: recurso_opciones[i])
                if sel_idx > 0:
                    asignado_a_id = recurso_ids[sel_idx]
                sla_rpta = c6.selectbox("SLA Respuesta", list(SLA_RESPUESTA.keys()), index=1)
            else:
                c4, c5 = st.columns(2)
                destinatario = c4.text_input("Destinatario")
                sla_rpta = c5.selectbox("SLA Respuesta", list(SLA_RESPUESTA.keys()), index=1)
            desc = st.text_area("Descripción / Notas", height=80)
            if st.form_submit_button("Guardar Actividad"):
                sla_hours = _sla_to_hours(sla_key)
                new_act = dal.create_activity(opp["id"], team_id, user_id, {
                    "tipo": tipo, "fecha": str(fecha), "objetivo": objetivo,
                    "descripcion": desc, "sla_key": sla_key, "sla_hours": sla_hours,
                    "sla_respuesta_dias": SLA_RESPUESTA[sla_rpta],
                    "destinatario": destinatario, "assigned_to": asignado_a_id,
                })
                if asignado_a_id and new_act:
                    assignee = dal.get_team_member(asignado_a_id)
                    if assignee:
                        notifications.send_assignment_notification(new_act, assignee, opp)
                        dal.create_notification(team_id, new_act["id"], asignado_a_id, "assignment")
                st.session_state.pop("show_new_act", None)
                st.rerun()

else:
    # --- VISTAS PRINCIPALES ---
    tabs = ["📊 Tablero", "📋 Actividades"]
    if has_control_access():
        tabs.append("📈 Control")
    tabs.append("👥 Equipo")

    selected_tabs = st.tabs(tabs)

    # --- TAB: TABLERO ---
    with selected_tabs[0]:
        st.markdown(user_bar_html, unsafe_allow_html=True)
        if can_see_all_opportunities():
            all_opps = dal.get_opportunities(team_id)
        else:
            all_opps = dal.get_opportunities_for_user(team_id, user_id, user["role"])
        # Precargar actividades para todas las oportunidades
        all_acts_by_opp = {}
        if can_see_all_opportunities():
            all_activities = dal.get_all_activities(team_id)
        else:
            all_activities = dal.get_all_activities_for_user(team_id, user_id, user["role"])
        for act in all_activities:
            all_acts_by_opp.setdefault(act["opportunity_id"], []).append(act)

        # Category focus: show buttons to toggle
        focused = st.session_state.focused_cat
        if focused:
            visible_cats = [focused]
        else:
            visible_cats = CATEGORIAS

        # Category selector buttons (styled via JS in components.html)
        btn_cols = st.columns(len(CATEGORIAS))
        for i, bc in enumerate(btn_cols):
            cat = CATEGORIAS[i]
            if focused == cat:
                if bc.button(f"✕ {cat} — Ver todas", key=f"unfocus_{cat}", use_container_width=True):
                    st.session_state.focused_cat = None
                    st.rerun()
            else:
                if bc.button(cat, key=f"focus_{cat}", use_container_width=True):
                    st.session_state.focused_cat = cat
                    st.rerun()

        # --- Bulk delete ---
        opp_options = {o["id"]: f'{o["proyecto"]} — {o["cuenta"]}' for o in all_opps}
        bulk_sel_col, bulk_act_col = st.columns([0.75, 0.25])
        with bulk_sel_col:
            bulk_ids = st.multiselect(
                "Seleccionar para eliminar",
                options=list(opp_options.keys()),
                format_func=lambda oid: opp_options.get(oid, oid),
                key="bulk_del_select",
                placeholder="Seleccionar scorecards para eliminar en lote...",
                label_visibility="collapsed",
            )
        with bulk_act_col:
            if bulk_ids:
                if st.button(f"🗑 Eliminar {len(bulk_ids)} seleccionados", key="bulk_del_btn", use_container_width=True, type="primary"):
                    st.session_state.bulk_del_confirm = list(bulk_ids)
                    st.rerun()
        if st.session_state.get("bulk_del_confirm"):
            ids_to_del = st.session_state.bulk_del_confirm
            names = [opp_options.get(oid, oid) for oid in ids_to_del]
            st.warning(f"¿Eliminar **{len(ids_to_del)}** oportunidades?\n\n" + ", ".join(names))
            bd1, bd2 = st.columns(2)
            if bd1.button("Confirmar eliminación", key="bulk_del_yes", use_container_width=True):
                for oid in ids_to_del:
                    dal.delete_opportunity(oid)
                st.session_state.pop("bulk_del_confirm", None)
                st.rerun()
            if bd2.button("Cancelar", key="bulk_del_no", use_container_width=True):
                st.session_state.pop("bulk_del_confirm", None)
                st.rerun()

        def _render_account_group(cuenta, opps, all_acts_by_opp):
            """Renders one account group with its opportunity cards."""
            total = sum(float(o.get('monto') or 0) for o in opps)
            badge = f'<span class="account-badge">{len(opps)} opp{"s" if len(opps) > 1 else ""}</span>' if len(opps) > 1 else ""
            import re
            safe_cuenta = re.sub(r'[^a-zA-Z0-9]', '_', cuenta)
            st.markdown(f'<div class="account-group"><div class="account-header"><span class="account-name">{cuenta}</span><span class="account-total">USD {total:,.0f}</span>{badge}</div>', unsafe_allow_html=True)
            for o in opps:
                opp_acts = all_acts_by_opp.get(o["id"], [])
                monto_val = float(o.get("monto") or 0)
                # Build HTML card — left: name + stage/amount, right: opp_id + close date
                name_html = f'<div class="opp-name">{o["proyecto"]}</div>'
                stage_html = f'<span class="stage-badge">{o["stage"]}</span>' if o.get("stage") else ""
                row2_html = f'<div class="opp-row2">{stage_html}<span class="amount">USD {monto_val:,.0f}</span></div>'
                # Right side: opp ID + close date stacked
                right_parts = []
                if o.get("opp_id"):
                    right_parts.append(f'<span class="opp-id-box">{o["opp_id"]}</span>')
                if o.get("close_date"):
                    right_parts.append(f'<span class="close-date">Cierre: {o["close_date"]}</span>')
                right_html = f'<div class="opp-right">{"".join(right_parts)}</div>' if right_parts else ""
                header_html = f'<div class="opp-top"><div class="opp-left">{name_html}{row2_html}</div>{right_html}</div>'
                meta_html = ""
                # Activities
                act_lines = []
                for a in opp_acts:
                    light, label = _traffic_light(a)
                    obj = f' <span class="act-obj">{a["objetivo"]}</span>' if a.get("objetivo") else ""
                    dest = f' → <span class="act-dest">{a["destinatario"]}</span>' if a.get("destinatario") else ""
                    asig_name = ""
                    if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                        asig_name = a["assigned_profile"]["full_name"]
                    asig_init = _get_initials(asig_name) if asig_name else ""
                    asig = f' <span class="act-asig">{asig_init}</span>' if asig_init else ""
                    status_html = f'<span class="act-status">{label}</span>'
                    # Color border-left by activity type
                    tipo = a.get("tipo", "")
                    border_colors = {"Email": "#3b82f6", "Llamada": "#f59e0b", "Reunión": "#10b981", "Asignación": "#8b5cf6"}
                    border_color = border_colors.get(tipo, "#cbd5e1")
                    act_lines.append(f'<div class="act-line" style="border-left-color:{border_color};">{light}{obj}{dest}{asig} — {status_html}</div>')
                acts_html = ""
                if act_lines:
                    acts_html = '<div class="act-sep"></div>' + "".join(act_lines)
                del_icon = '<span class="card-del-trigger">&times;</span>'
                card_html = f'<div class="pgm-card-wrap">{del_icon}{header_html}{meta_html}{acts_html}</div>'
                st.markdown(card_html, unsafe_allow_html=True)
                c_open, c_del = st.columns([0.92, 0.08])
                if c_open.button("▸", key=f"g_{o['id']}", use_container_width=True):
                    st.session_state.selected_id = o['id']
                    st.rerun()
                if c_del.button("×", key=f"qd_{o['id']}", use_container_width=True):
                    st.session_state[f"quick_del_{o['id']}"] = True
                    st.rerun()
                # Delete confirmation
                if st.session_state.get(f"quick_del_{o['id']}"):
                    st.warning(f"Eliminar **{o['proyecto']}**?")
                    qd1, qd2 = st.columns(2)
                    if qd1.button("Confirmar", key=f"qdy_{o['id']}", use_container_width=True):
                        dal.delete_opportunity(o["id"])
                        st.session_state.pop(f"quick_del_{o['id']}", None)
                        st.rerun()
                    if qd2.button("Cancelar", key=f"qdn_{o['id']}", use_container_width=True):
                        st.session_state.pop(f"quick_del_{o['id']}", None)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if focused:
            # Focused mode: single category
            cat = visible_cats[0]
            items = [o for o in all_opps if o['categoria'] == cat]
            accounts = OrderedDict()
            for o in sorted(items, key=lambda x: float(x.get('monto') or 0), reverse=True):
                accounts.setdefault(o['cuenta'], []).append(o)
            account_list = list(accounts.items())
            if is_mobile:
                for cuenta, opps in account_list:
                    _render_account_group(cuenta, opps, all_acts_by_opp)
            else:
                col_left, col_right = st.columns(2)
                for idx, (cuenta, opps) in enumerate(account_list):
                    with col_left if idx % 2 == 0 else col_right:
                        _render_account_group(cuenta, opps, all_acts_by_opp)
        else:
            if is_mobile:
                # Mobile: single column, categories stacked
                for cat in visible_cats:
                    items = [o for o in all_opps if o['categoria'] == cat]
                    if items:
                        accounts = OrderedDict()
                        for o in sorted(items, key=lambda x: float(x.get('monto') or 0), reverse=True):
                            accounts.setdefault(o['cuenta'], []).append(o)
                        for cuenta, opps in accounts.items():
                            _render_account_group(cuenta, opps, all_acts_by_opp)
            else:
                # Desktop: one column per category
                cols = st.columns(len(visible_cats))
                for i, col in enumerate(cols):
                    with col:
                        cat = visible_cats[i]
                        items = [o for o in all_opps if o['categoria'] == cat]
                        accounts = OrderedDict()
                        for o in sorted(items, key=lambda x: float(x.get('monto') or 0), reverse=True):
                            accounts.setdefault(o['cuenta'], []).append(o)
                        for cuenta, opps in accounts.items():
                            _render_account_group(cuenta, opps, all_acts_by_opp)

    # --- TAB: ACTIVIDADES ---
    with selected_tabs[1]:
        st.markdown(user_bar_html, unsafe_allow_html=True)

        ALL_COLUMNS = ["Semáforo", "Estado", "Categoría", "Cuenta", "Proyecto", "Monto USD", "Canal", "Objetivo", "Destinatario", "Asignado a", "Fecha", "SLA", "SLA Respuesta (días)", "Estado Interno", "Feedback", "Descripción"]
        DEFAULT_COLUMNS = ["Semáforo", "Estado", "Categoría", "Cuenta", "Proyecto", "Canal", "Objetivo", "Destinatario", "Fecha", "Estado Interno"]

        # Filter: my tasks vs team tasks
        scope_options = ["📋 Mis tareas", "👥 Tareas del equipo", "🌐 Todas"]
        act_scope = st.radio("Vista", scope_options, horizontal=True, key="act_scope", index=2)

        if can_see_all_opportunities():
            all_activities_full = dal.get_all_activities(team_id)
        else:
            all_activities_full = dal.get_all_activities_for_user(team_id, user_id, user["role"])

        # Apply scope filter
        if act_scope == "📋 Mis tareas":
            all_activities_full = [a for a in all_activities_full if a.get("assigned_to") == user_id or a.get("created_by") == user_id]
        elif act_scope == "👥 Tareas del equipo":
            all_activities_full = [a for a in all_activities_full if a.get("assigned_to") != user_id and a.get("created_by") != user_id]

        all_acts_display = []
        act_refs = []
        for a in all_activities_full:
            opp_data = a.get("opportunity", {}) or {}
            light, label = _traffic_light(a)
            assigned_name = ""
            if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                assigned_name = a["assigned_profile"]["full_name"]

            all_acts_display.append({
                "Semáforo": light,
                "Estado": label,
                "Categoría": opp_data.get("categoria", ""),
                "Cuenta": opp_data.get("cuenta", ""),
                "Proyecto": opp_data.get("proyecto", ""),
                "Monto USD": opp_data.get("monto", 0),
                "Canal": a.get("tipo", ""),
                "Objetivo": a.get("objetivo", ""),
                "Destinatario": a.get("destinatario", ""),
                "Asignado a": assigned_name,
                "Fecha": str(a.get("fecha", "")),
                "SLA": a.get("sla_key", ""),
                "SLA Respuesta (días)": a.get("sla_respuesta_dias", ""),
                "Estado Interno": a.get("estado", ""),
                "Feedback": a.get("feedback", ""),
                "Descripción": a.get("descripcion", ""),
            })
            act_refs.append(a)

        if not all_acts_display:
            st.info("No hay actividades registradas aún.")
        else:
            if 'act_columns' not in st.session_state:
                st.session_state.act_columns = DEFAULT_COLUMNS
            selected_cols = st.multiselect("Columnas visibles", ALL_COLUMNS, default=st.session_state.act_columns, key="col_selector")
            st.session_state.act_columns = selected_cols

            fc1, fc2, fc3, fc4 = st.columns(4)
            cats_disponibles = sorted(set(r["Categoría"] for r in all_acts_display))
            fil_cat = fc1.multiselect("Categoría", cats_disponibles, default=cats_disponibles)
            estados_disponibles = sorted(set(r["Estado Interno"] for r in all_acts_display))
            fil_estado = fc2.multiselect("Estado", estados_disponibles, default=estados_disponibles)
            canales_disponibles = sorted(set(r["Canal"] for r in all_acts_display))
            fil_canal = fc3.multiselect("Canal", canales_disponibles, default=canales_disponibles)
            cuentas_disponibles = sorted(set(r["Cuenta"] for r in all_acts_display))
            fil_cuenta = fc4.multiselect("Cuenta", cuentas_disponibles, default=cuentas_disponibles)

            df_acts = pd.DataFrame(all_acts_display)
            mask = (
                (df_acts["Categoría"].isin(fil_cat)) &
                (df_acts["Estado Interno"].isin(fil_estado)) &
                (df_acts["Canal"].isin(fil_canal)) &
                (df_acts["Cuenta"].isin(fil_cuenta))
            )
            df_filtered = df_acts[mask]

            st.divider()
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total", len(df_filtered))
            m2.metric("Pendientes", len(df_filtered[df_filtered["Estado Interno"] == "Pendiente"]))
            m3.metric("Enviadas", len(df_filtered[df_filtered["Estado Interno"] == "Enviada"]))
            m4.metric("Respondidas", len(df_filtered[df_filtered["Estado Interno"] == "Respondida"]))
            m5.metric("🟥 Bloqueadas/Vencidas", len(df_filtered[df_filtered["Estado"].isin(["Bloqueada", "Vencida"])]))

            st.divider()
            sorted_indices = df_filtered.sort_values("Fecha", ascending=False).index.tolist() if "Fecha" in df_filtered.columns else df_filtered.index.tolist()
            display_cols = [c for c in selected_cols if c in df_filtered.columns]

            n_cols = len(display_cols)
            widths = [1.0 / n_cols] * n_cols + [0.04] if n_cols else [1, 0.04]
            hdr_cols = st.columns(widths)
            for j, c in enumerate(display_cols):
                hdr_cols[j].markdown(f'<div style="font-size:0.7rem; font-weight:700; color:#64748b; text-transform:uppercase;">{c}</div>', unsafe_allow_html=True)

            for row_idx in sorted_indices:
                row = all_acts_display[row_idx]
                a_ref = act_refs[row_idx]
                row_cols = st.columns(widths)
                for j, c in enumerate(display_cols):
                    row_cols[j].markdown(f'<div style="font-size:0.8rem; padding:4px 0; border-bottom:1px solid #e2e8f0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{row.get(c, "")}</div>', unsafe_allow_html=True)
                if row_cols[-1].button("✏️", key=f"eab_{row_idx}"):
                    st.session_state["edit_act_tab_idx"] = row_idx

                if st.session_state.get("edit_act_tab_idx") == row_idx:
                    with st.form(f"edit_act_tab_{row_idx}"):
                        ea_c1, ea_c2, ea_c3 = st.columns(3)
                        ea_tipo = ea_c1.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"],
                            index=["Email", "Llamada", "Reunión", "Asignación"].index(a_ref.get("tipo", "Email")) if a_ref.get("tipo") in ["Email", "Llamada", "Reunión", "Asignación"] else 0)
                        sla_keys = list(SLA_OPCIONES.keys())
                        ea_sla = ea_c2.selectbox("SLA", sla_keys,
                            index=sla_keys.index(a_ref["sla_key"]) if a_ref.get("sla_key") in sla_keys else 0)
                        ea_fecha = ea_c3.date_input("Fecha", value=_parse_date(a_ref.get("fecha", "")) or date.today())
                        ea_objetivo = st.text_input("Objetivo", value=a_ref.get("objetivo", ""))
                        ea_c4, ea_c5, ea_c6 = st.columns(3)
                        ea_dest = ea_c4.text_input("Destinatario", value=a_ref.get("destinatario", ""))
                        # Asignado selector
                        recurso_opciones_tab = [""] + list(RECURSOS_PRESALES.values())
                        recurso_ids_tab = [""] + list(RECURSOS_PRESALES.keys())
                        current_assigned = a_ref.get("assigned_to", "")
                        assigned_idx = 0
                        if current_assigned and current_assigned in recurso_ids_tab:
                            assigned_idx = recurso_ids_tab.index(current_assigned)
                        ea_asig_idx = ea_c5.selectbox("Asignado a", range(len(recurso_opciones_tab)), format_func=lambda i: recurso_opciones_tab[i], index=assigned_idx)
                        sla_rpta_keys = list(SLA_RESPUESTA.keys())
                        sla_rpta_vals = list(SLA_RESPUESTA.values())
                        cur_sla_idx = sla_rpta_vals.index(a_ref.get("sla_respuesta_dias", 7)) if a_ref.get("sla_respuesta_dias", 7) in sla_rpta_vals else 1
                        ea_sla_rpta = ea_c6.selectbox("SLA Respuesta", sla_rpta_keys, index=cur_sla_idx)
                        ea_estado = st.selectbox("Estado", ["Pendiente", "Enviada", "Respondida"],
                            index=["Pendiente", "Enviada", "Respondida"].index(a_ref.get("estado", "Pendiente")) if a_ref.get("estado") in ["Pendiente", "Enviada", "Respondida"] else 0)
                        ea_feedback = st.text_area("Feedback", value=a_ref.get("feedback", ""))
                        ea_desc = st.text_area("Descripción", value=a_ref.get("descripcion", ""))
                        if st.form_submit_button("💾 Guardar"):
                            new_assigned = recurso_ids_tab[ea_asig_idx] if ea_asig_idx > 0 else None
                            new_sla_hours = _sla_to_hours(ea_sla)
                            dal.update_activity(a_ref["id"], {
                                "tipo": ea_tipo, "sla_key": ea_sla, "sla_hours": new_sla_hours,
                                "fecha": str(ea_fecha), "objetivo": ea_objetivo,
                                "destinatario": ea_dest, "assigned_to": new_assigned,
                                "sla_respuesta_dias": SLA_RESPUESTA[ea_sla_rpta],
                                "estado": ea_estado, "feedback": ea_feedback,
                                "descripcion": ea_desc,
                            })
                            st.session_state.pop("edit_act_tab_idx", None)
                            st.rerun()
                    if st.button("❌ Cerrar", key=f"close_eab_{row_idx}"):
                        st.session_state.pop("edit_act_tab_idx", None)
                        st.rerun()

    # --- TAB: CONTROL (admin, vp, y managers) ---
    if has_control_access():
        with selected_tabs[2]:
            st.markdown(user_bar_html, unsafe_allow_html=True)
            st.markdown("### 📈 Panel de Control — RSM")

            # Fetch all activities for the team
            ctrl_activities = dal.get_all_activities(team_id)
            today = date.today()
            now = datetime.now()

            # --- Helpers ---
            def _act_date(a):
                """Parse activity date to date object."""
                f = a.get("fecha")
                if isinstance(f, date):
                    return f
                return _parse_date(f) or today

            def _completed_ts(a):
                """Get the timestamp when activity was marked Respondida (updated_at)."""
                ts = a.get("updated_at") or a.get("created_at")
                if isinstance(ts, str):
                    try:
                        return datetime.fromisoformat(ts).date()
                    except Exception:
                        return None
                if isinstance(ts, datetime):
                    return ts.date()
                return None

            # Classify activities
            pendientes = [a for a in ctrl_activities if a.get("estado") == "Pendiente"]
            enviadas = [a for a in ctrl_activities if a.get("estado") == "Enviada"]
            respondidas = [a for a in ctrl_activities if a.get("estado") == "Respondida"]
            bloqueadas = [a for a in ctrl_activities if a.get("estado") == "Enviada" and _traffic_light(a)[1] == "Bloqueada"]

            # --- Section 1: Overview Metrics ---
            st.markdown("#### Resumen General")
            ov1, ov2, ov3, ov4 = st.columns(4)
            ov1.metric("Total Actividades", len(ctrl_activities))
            ov2.metric("Pendientes", len(pendientes))
            ov3.metric("Enviadas (Esp. rpta)", len(enviadas))
            ov4.metric("Respondidas", len(respondidas))

            if bloqueadas:
                st.error(f"🟥 **{len(bloqueadas)} actividades BLOQUEADAS** — respuesta vencida")

            st.divider()

            # --- Section 2: Activity by Day ---
            st.markdown("#### Actividad por Día")

            # Group activities by fecha for recent days
            day_range = [today - timedelta(days=i) for i in range(7)]
            day_labels = []
            day_created = []
            day_completed = []
            day_enviadas = []

            for d in reversed(day_range):
                day_labels.append(d.strftime("%a %d/%m"))
                day_created.append(len([a for a in ctrl_activities if _act_date(a) == d]))
                day_completed.append(len([a for a in respondidas if _completed_ts(a) == d]))
                day_enviadas.append(len([a for a in enviadas if _act_date(a) == d]))

            df_daily = pd.DataFrame({
                "Día": day_labels,
                "Programadas": day_created,
                "Enviadas": day_enviadas,
                "Respondidas": day_completed,
            })
            st.bar_chart(df_daily.set_index("Día"), color=["#f59e0b", "#8b5cf6", "#16a34a"])

            # Day metrics
            acts_today = [a for a in ctrl_activities if _act_date(a) == today]
            acts_yesterday = [a for a in ctrl_activities if _act_date(a) == today - timedelta(days=1)]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Hoy — Programadas", len(acts_today))
            d2.metric("Hoy — Respondidas", len([a for a in respondidas if _completed_ts(a) == today]))
            d3.metric("Ayer — Programadas", len(acts_yesterday))
            d4.metric("Ayer — Respondidas", len([a for a in respondidas if _completed_ts(a) == today - timedelta(days=1)]))

            st.divider()

            # --- Section 3: Weekly Summary ---
            st.markdown("#### Resumen Semanal")

            # Current week (Mon-Sun)
            week_start = today - timedelta(days=today.weekday())
            last_week_start = week_start - timedelta(days=7)

            this_week = [a for a in ctrl_activities if week_start <= _act_date(a) <= today]
            last_week = [a for a in ctrl_activities if last_week_start <= _act_date(a) < week_start]
            this_week_resp = [a for a in respondidas if _completed_ts(a) and week_start <= _completed_ts(a) <= today]
            last_week_resp = [a for a in respondidas if _completed_ts(a) and last_week_start <= _completed_ts(a) < week_start]

            w1, w2, w3, w4 = st.columns(4)
            w1.metric("Esta semana — Programadas", len(this_week),
                       delta=f"{len(this_week) - len(last_week):+d} vs semana anterior")
            w2.metric("Esta semana — Respondidas", len(this_week_resp),
                       delta=f"{len(this_week_resp) - len(last_week_resp):+d} vs semana anterior")
            w3.metric("Semana anterior — Programadas", len(last_week))
            w4.metric("Semana anterior — Respondidas", len(last_week_resp))

            # Completion rate
            if this_week:
                this_rate = len(this_week_resp) / len(this_week) * 100
                st.progress(min(this_rate / 100, 1.0), text=f"Tasa de cierre esta semana: **{this_rate:.0f}%** ({len(this_week_resp)}/{len(this_week)})")

            st.divider()

            # --- Section 4: Upcoming Schedule ---
            st.markdown("#### Próximas Actividades Programadas")

            upcoming_7 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=7)]
            upcoming_14 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=14)]
            upcoming_30 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=30)]
            overdue = [a for a in pendientes if _act_date(a) < today]

            u1, u2, u3, u4 = st.columns(4)
            u1.metric("Próx. 7 días", len(upcoming_7))
            u2.metric("Próx. 14 días", len(upcoming_14))
            u3.metric("Próx. 30 días", len(upcoming_30))
            u4.metric("⚠️ Vencidas (sin enviar)", len(overdue), delta=f"-{len(overdue)}" if overdue else "0", delta_color="inverse")

            st.divider()

            # --- Section 5: Team Member Breakdown ---
            st.markdown("#### Rendimiento por Miembro")

            member_stats = {}
            for m in team_members:
                mid = m["id"]
                mname = m["full_name"]
                m_acts = [a for a in ctrl_activities if a.get("assigned_to") == mid or a.get("created_by") == mid]
                m_pend = len([a for a in m_acts if a.get("estado") == "Pendiente"])
                m_env = len([a for a in m_acts if a.get("estado") == "Enviada"])
                m_resp = len([a for a in m_acts if a.get("estado") == "Respondida"])
                m_bloq = len([a for a in m_acts if a.get("estado") == "Enviada" and _traffic_light(a)[1] == "Bloqueada"])
                m_overdue = len([a for a in m_acts if a.get("estado") == "Pendiente" and _act_date(a) < today])
                m_upcoming = len([a for a in m_acts if a.get("estado") == "Pendiente" and today <= _act_date(a) <= today + timedelta(days=7)])
                total = len(m_acts)
                rate = (m_resp / total * 100) if total > 0 else 0
                member_stats[mname] = {
                    "Total": total,
                    "Pendientes": m_pend,
                    "Enviadas": m_env,
                    "Respondidas": m_resp,
                    "Bloqueadas": m_bloq,
                    "Vencidas": m_overdue,
                    "Próx. 7d": m_upcoming,
                    "% Cierre": f"{rate:.0f}%",
                }

            if member_stats:
                df_members = pd.DataFrame(member_stats).T
                df_members.index.name = "Miembro"
                st.dataframe(df_members, use_container_width=True)

                # Bar chart: respondidas by member
                resp_by_member = {name: stats["Respondidas"] for name, stats in member_stats.items() if stats["Total"] > 0}
                if resp_by_member:
                    st.markdown("##### Actividades Respondidas por Miembro")
                    df_resp_chart = pd.DataFrame({"Miembro": list(resp_by_member.keys()), "Respondidas": list(resp_by_member.values())})
                    st.bar_chart(df_resp_chart.set_index("Miembro"), color=["#16a34a"])

    # --- TAB: EQUIPO (todos los roles) ---
    equipo_tab_idx = 3 if has_control_access() else 2
    with selected_tabs[equipo_tab_idx]:
        st.markdown(user_bar_html, unsafe_allow_html=True)
        team_info = dal.get_team(team_id)

        # Sub-tabs según rol
        if is_admin():
            equipo_subtabs = st.tabs(["👥 Miembros", "🏢 Equipos", "⚙️ Configuración", "📨 Invitaciones"])
        else:
            equipo_subtabs = st.tabs(["👥 Miembros", "📨 Invitaciones"])

        # --- MIEMBROS ---
        with equipo_subtabs[0]:
            st.subheader("Miembros del Equipo")
            members = dal.get_team_members(team_id, active_only=False)

            if team_info:
                st.caption(f"Equipo: **{team_info['name']}** — ID: `{team_id}`")

            if is_admin():
                # Admin: edición completa con todos los roles
                for m in members:
                    m_role_label = ROLE_LABELS.get(m['role'], m['role'])
                    with st.expander(f"{'🟢' if m['active'] else '🔴'} {m['full_name']} — {m_role_label} {'(' + m['specialty'] + ')' if m.get('specialty') else ''}"):
                        with st.form(f"edit_member_{m['id']}"):
                            mc1, mc2 = st.columns(2)
                            m_name = mc1.text_input("Nombre", value=m["full_name"], key=f"mn_{m['id']}")
                            m_email = mc2.text_input("Email", value=m["email"], key=f"me_{m['id']}")
                            mc3, mc4, mc5 = st.columns(3)
                            m_role = mc3.selectbox("Rol", ALL_ROLES,
                                format_func=lambda r: ROLE_LABELS.get(r, r),
                                index=ALL_ROLES.index(m["role"]) if m["role"] in ALL_ROLES else len(ALL_ROLES) - 1,
                                key=f"mr_{m['id']}")
                            m_specialty = mc4.text_input("Especialidad", value=m.get("specialty", ""), key=f"ms_{m['id']}")
                            m_phone = mc5.text_input("Teléfono", value=m.get("phone", ""), key=f"mp_{m['id']}")
                            m_active = st.checkbox("Activo", value=m["active"], key=f"ma_{m['id']}")
                            if st.form_submit_button("💾 Guardar"):
                                dal.update_team_member(m["id"], {
                                    "full_name": m_name, "role": m_role,
                                    "specialty": m_specialty, "phone": m_phone,
                                    "active": m_active,
                                })
                                st.success("Miembro actualizado.")
                                st.rerun()
                        # Eliminar miembro (no puede eliminarse a sí mismo)
                        if m["id"] != user_id:
                            if st.button("🗑️ Eliminar miembro", key=f"del_member_{m['id']}"):
                                st.session_state[f"confirm_del_member_{m['id']}"] = True
                            if st.session_state.get(f"confirm_del_member_{m['id']}"):
                                st.warning(f"Eliminar a **{m['full_name']}**? Se eliminará su perfil y cuenta.")
                                dm1, dm2 = st.columns(2)
                                if dm1.button("Confirmar", key=f"cdel_m_y_{m['id']}", use_container_width=True):
                                    dal.delete_team_member(m["id"])
                                    st.session_state.pop(f"confirm_del_member_{m['id']}", None)
                                    st.rerun()
                                if dm2.button("Cancelar", key=f"cdel_m_n_{m['id']}", use_container_width=True):
                                    st.session_state.pop(f"confirm_del_member_{m['id']}", None)
                                    st.rerun()
            else:
                # Otros roles: vista de solo lectura
                active_members = [m for m in members if m["active"]]
                role_emojis = {"admin": "🔑", "vp": "🏛️", "account_manager": "📊", "regional_sales_manager": "🌎", "partner_manager": "🤝", "regional_partner_manager": "🌐", "presales_manager": "📋", "presales": "💼"}
                for m in active_members:
                    role_emoji = role_emojis.get(m["role"], "👤")
                    m_role_label = ROLE_LABELS.get(m['role'], m['role'])
                    specialty_txt = f" · {m['specialty']}" if m.get("specialty") else ""
                    st.markdown(f"{role_emoji} **{m['full_name']}** — {m_role_label}{specialty_txt}")

        # --- EQUIPOS (solo admin) ---
        if is_admin():
            with equipo_subtabs[1]:
                st.subheader("Gestión de Equipos")

                # --- Editar equipo actual ---
                st.markdown("#### Equipo Actual")
                with st.form("edit_team_form"):
                    et_name = st.text_input("Nombre del equipo", value=team_info["name"] if team_info else "", key="edit_team_name")
                    if st.form_submit_button("💾 Guardar Nombre"):
                        if et_name.strip():
                            dal.update_team(team_id, {"name": et_name.strip()})
                            st.success("Nombre del equipo actualizado.")
                            st.rerun()
                        else:
                            st.error("El nombre no puede estar vacío.")

                st.divider()

                # --- Crear nuevo equipo ---
                st.markdown("#### Crear Nuevo Equipo")
                with st.form("create_team_form"):
                    new_team_name = st.text_input("Nombre del nuevo equipo", key="new_team_name")
                    if st.form_submit_button("➕ Crear Equipo"):
                        if new_team_name.strip():
                            new_team = dal.create_team(new_team_name.strip())
                            if new_team:
                                st.success(f"Equipo **{new_team_name}** creado. ID: `{new_team['id']}`")
                                st.rerun()
                            else:
                                st.error("No se pudo crear el equipo.")
                        else:
                            st.error("Ingresa un nombre para el equipo.")

                st.divider()

                # --- Lista de todos los equipos con cobertura de roles ---
                st.markdown("#### Todos los Equipos")
                all_teams = dal.get_all_teams()
                for t in all_teams:
                    is_current = t["id"] == team_id
                    team_label = f"{'🔹 ' if is_current else ''}{t['name']}"
                    t_members = dal.get_all_members_for_team(t["id"])
                    active_members = [m for m in t_members if m.get("active", True)]
                    filled_roles = {m["role"] for m in active_members}
                    missing_roles = [r for r in ALL_ROLES if r not in filled_roles]

                    with st.expander(f"{team_label} — {len(active_members)} miembros" + (" (actual)" if is_current else "")):
                        st.caption(f"ID: `{t['id']}`")

                        # Cobertura de roles
                        if missing_roles:
                            missing_labels = ", ".join(ROLE_LABELS.get(r, r) for r in missing_roles)
                            st.warning(f"Roles sin cubrir: {missing_labels}")
                        else:
                            st.success("Todos los roles cubiertos")

                        # Tabla de miembros (editable)
                        if t_members:
                            for m in t_members:
                                m_role_label = ROLE_LABELS.get(m["role"], m["role"])
                                status_icon = "🟢" if m.get("active", True) else "🔴"
                                with st.expander(f"{status_icon} {m['full_name']} — {m_role_label} {'(' + m['specialty'] + ')' if m.get('specialty') else ''}"):
                                    with st.form(f"edit_tm_{t['id']}_{m['id']}"):
                                        tm_c1, tm_c2 = st.columns(2)
                                        tm_name = tm_c1.text_input("Nombre", value=m["full_name"], key=f"tmn_{t['id']}_{m['id']}")
                                        tm_email = tm_c2.text_input("Email", value=m.get("email", ""), key=f"tme_{t['id']}_{m['id']}")
                                        tm_c3, tm_c4, tm_c5 = st.columns(3)
                                        tm_role = tm_c3.selectbox("Rol", ALL_ROLES,
                                            format_func=lambda r: ROLE_LABELS.get(r, r),
                                            index=ALL_ROLES.index(m["role"]) if m["role"] in ALL_ROLES else len(ALL_ROLES) - 1,
                                            key=f"tmr_{t['id']}_{m['id']}")
                                        tm_specialty = tm_c4.text_input("Especialidad", value=m.get("specialty", ""), key=f"tms_{t['id']}_{m['id']}")
                                        tm_phone = tm_c5.text_input("Teléfono", value=m.get("phone", ""), key=f"tmp_{t['id']}_{m['id']}")
                                        tm_active = st.checkbox("Activo", value=m.get("active", True), key=f"tma_{t['id']}_{m['id']}")
                                        if st.form_submit_button("💾 Guardar"):
                                            dal.update_team_member(m["id"], {
                                                "full_name": tm_name, "role": tm_role,
                                                "specialty": tm_specialty, "phone": tm_phone,
                                                "active": tm_active,
                                            })
                                            st.success("Miembro actualizado.")
                                            st.rerun()
                                    # Eliminar miembro (no puede eliminarse a sí mismo)
                                    if m["id"] != user_id:
                                        if st.button("🗑️ Eliminar", key=f"del_tm_{t['id']}_{m['id']}"):
                                            st.session_state[f"confirm_del_tm_{t['id']}_{m['id']}"] = True
                                        if st.session_state.get(f"confirm_del_tm_{t['id']}_{m['id']}"):
                                            st.warning(f"Eliminar a **{m['full_name']}**?")
                                            dtm1, dtm2 = st.columns(2)
                                            if dtm1.button("Confirmar", key=f"cdel_tm_y_{t['id']}_{m['id']}", use_container_width=True):
                                                dal.delete_team_member(m["id"])
                                                st.session_state.pop(f"confirm_del_tm_{t['id']}_{m['id']}", None)
                                                st.rerun()
                                            if dtm2.button("Cancelar", key=f"cdel_tm_n_{t['id']}_{m['id']}", use_container_width=True):
                                                st.session_state.pop(f"confirm_del_tm_{t['id']}_{m['id']}", None)
                                                st.rerun()

                            # Mover miembro a otro equipo
                            if len(all_teams) > 1:
                                st.markdown("---")
                                st.markdown("**Mover miembro a otro equipo:**")
                                member_options = {m["id"]: m["full_name"] for m in t_members}
                                other_teams = {ot["id"]: ot["name"] for ot in all_teams if ot["id"] != t["id"]}
                                with st.form(f"move_member_{t['id']}"):
                                    mm_c1, mm_c2 = st.columns(2)
                                    member_ids = list(member_options.keys())
                                    member_names = list(member_options.values())
                                    sel_member = mm_c1.selectbox("Miembro", member_ids, format_func=lambda mid: member_options[mid], key=f"sel_mm_{t['id']}")
                                    dest_team_ids = list(other_teams.keys())
                                    sel_dest = mm_c2.selectbox("Equipo destino", dest_team_ids, format_func=lambda tid: other_teams[tid], key=f"sel_dt_{t['id']}")
                                    if st.form_submit_button("🔀 Mover"):
                                        dal.move_member_to_team(sel_member, sel_dest)
                                        st.success(f"Miembro movido a **{other_teams[sel_dest]}**.")
                                        st.rerun()
                        else:
                            st.info("Sin miembros.")

                        # Eliminar equipo (solo si no es el actual y no tiene miembros)
                        if not is_current:
                            if not t_members:
                                if st.button(f"🗑️ Eliminar equipo", key=f"del_team_{t['id']}"):
                                    st.session_state[f"confirm_del_team_{t['id']}"] = True
                                if st.session_state.get(f"confirm_del_team_{t['id']}"):
                                    st.warning(f"Eliminar el equipo **{t['name']}**?")
                                    dtc1, dtc2 = st.columns(2)
                                    if dtc1.button("Confirmar", key=f"cdel_team_y_{t['id']}", use_container_width=True):
                                        dal.delete_team(t["id"])
                                        st.session_state.pop(f"confirm_del_team_{t['id']}", None)
                                        st.rerun()
                                    if dtc2.button("Cancelar", key=f"cdel_team_n_{t['id']}", use_container_width=True):
                                        st.session_state.pop(f"confirm_del_team_{t['id']}", None)
                                        st.rerun()
                            else:
                                st.caption("Para eliminar este equipo, primero mueve o elimina todos sus miembros.")

        # --- CONFIGURACIÓN (solo admin) ---
        if is_admin():
            with equipo_subtabs[2]:
                st.subheader("Configuración del Equipo")

                # SLA Opciones
                st.write("**Opciones de SLA**")
                sla_config = dal.get_sla_options(team_id)
                sla_json = st.text_area("SLA (JSON)", value=json.dumps(sla_config, ensure_ascii=False, indent=2), height=200, key="sla_config_edit")
                if st.button("Guardar SLA", key="save_sla"):
                    try:
                        parsed = json.loads(sla_json)
                        dal.set_team_config(team_id, "sla_opciones", parsed)
                        st.success("SLA actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

                st.divider()

                # SLA Respuesta
                st.write("**SLA de Respuesta**")
                sla_rpta_config = dal.get_sla_respuesta(team_id)
                sla_rpta_json = st.text_area("SLA Respuesta (JSON)", value=json.dumps(sla_rpta_config, ensure_ascii=False, indent=2), height=150, key="sla_rpta_config_edit")
                if st.button("Guardar SLA Respuesta", key="save_sla_rpta"):
                    try:
                        parsed = json.loads(sla_rpta_json)
                        dal.set_team_config(team_id, "sla_respuesta", parsed)
                        st.success("SLA Respuesta actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

                st.divider()

                # Categorías
                st.write("**Categorías**")
                cats_config = dal.get_categorias(team_id)
                cats_json = st.text_area("Categorías (JSON array)", value=json.dumps(cats_config, ensure_ascii=False, indent=2), height=100, key="cats_config_edit")
                if st.button("Guardar Categorías", key="save_cats"):
                    try:
                        parsed = json.loads(cats_json)
                        if isinstance(parsed, list):
                            dal.set_team_config(team_id, "categorias", parsed)
                            st.success("Categorías actualizadas.")
                            st.rerun()
                        else:
                            st.error("Debe ser un array JSON.")
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

        # --- INVITACIONES ---
        inv_subtab_idx = 3 if is_admin() else 1
        with equipo_subtabs[inv_subtab_idx]:
            st.subheader("Invitar Miembros")

            app_url = st.secrets.get("APP_URL", "https://your-app.streamlit.app")

            # Admin puede elegir a qué equipo invitar; otros solo a su equipo
            if is_admin():
                inv_all_teams = dal.get_all_teams()
                inv_team_options = {t["id"]: t["name"] for t in inv_all_teams}
                inv_team_ids = list(inv_team_options.keys())
                current_idx = inv_team_ids.index(team_id) if team_id in inv_team_ids else 0
                invite_target_id = st.selectbox(
                    "Equipo destino",
                    inv_team_ids,
                    format_func=lambda tid: inv_team_options[tid],
                    index=current_idx,
                    key="invite_target_team",
                )
                invite_target_name = inv_team_options.get(invite_target_id, "Equipo")
            else:
                invite_target_id = team_id
                invite_target_name = team_info['name'] if team_info else 'Equipo'

            if not has_control_access():
                st.info("Puedes invitar a otros miembros a unirse al equipo.")

            st.markdown(f"""
**Pasos para invitar a un nuevo miembro:**
1. Comparte el siguiente enlace y datos con el invitado
2. El invitado abre el enlace, selecciona **"Unirse a Equipo"** y se registra con el ID de equipo
""")
            inv_c1, inv_c2 = st.columns(2)
            inv_c1.text_input("Enlace de la app", value=app_url, disabled=True, key="invite_url")
            inv_c2.markdown(f"**ID de equipo**")
            inv_c2.code(invite_target_id)

            st.divider()

            # SendGrid email (optional) — real keys are 69+ chars like SG.xxx.yyy
            sg_key = st.secrets.get("SENDGRID_API_KEY", "")
            sg_configured = sg_key and len(sg_key) > 50 and sg_key.startswith("SG.")

            with st.expander("📨 Enviar invitación por email (opcional)"):
                if not sg_configured:
                    st.warning("SendGrid no está configurado. Para habilitar invitaciones por email, crea una cuenta gratuita en [sendgrid.com](https://sendgrid.com) y agrega tu API key en los secrets de la app.")
                else:
                    with st.form("invite_form"):
                        inv_email = st.text_input("Email del invitado")
                        inv_name = st.text_input("Nombre (opcional)")
                        if st.form_submit_button("📨 Enviar Invitación"):
                            if inv_email:
                                from sendgrid import SendGridAPIClient
                                from sendgrid.helpers.mail import Mail, Email, To, Content
                                try:
                                    sg = SendGridAPIClient(api_key=sg_key)
                                    message = Mail(
                                        from_email=Email(st.secrets.get("SENDGRID_FROM_EMAIL", "noreply@pgmachine.com"), st.secrets.get("SENDGRID_FROM_NAME", "PG Machine")),
                                        to_emails=To(inv_email),
                                        subject=f"Invitación a PG Machine — {invite_target_name}",
                                        html_content=Content("text/html", f'<div style="font-family:Inter,sans-serif;max-width:500px;margin:0 auto;"><div style="background:#1e293b;color:white;padding:20px;border-radius:8px 8px 0 0;text-align:center;"><h2>Invitación a PG Machine</h2></div><div style="background:white;padding:20px;border:1px solid #e2e8f0;border-radius:0 0 8px 8px;"><p>Hola{" " + inv_name if inv_name else ""},</p><p>Te han invitado a unirte al equipo <b>{invite_target_name}</b> en PG Machine.</p><p>Para registrarte, abre la app y selecciona "Unirse a Equipo":</p><p><b>ID del equipo:</b> <code>{invite_target_id}</code></p><div style="text-align:center;margin:20px 0;"><a href="{app_url}" style="background:#1a73e8;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Ir a PG Machine</a></div></div></div>')
                                    )
                                    sg.send(message)
                                    st.success(f"Invitación enviada a {inv_email} para el equipo **{invite_target_name}**")
                                except Exception as e:
                                    st.error(f"Error enviando email: {e}")
                            else:
                                st.error("Ingresa un email.")
