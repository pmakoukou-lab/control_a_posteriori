/* ====================================================================
   AUDIT a posteriori — JavaScript global (partagé par toutes les pages)
   Gère : état actif de la navigation, sous-menu Administration,
          listes déroulantes de l'en-tête (Gestion / Session),
          comboboxes (listes déroulantes avec recherche) — réf. collecte.
   Une page qui gère elle-même sa navigation (ex. comportements
   entrelacés) peut poser  window.AUDIT_PAGE_OWNS_NAV = true;  dans son
   propre block js pour désactiver UNIQUEMENT la navigation partagée.
   Les comboboxes, elles, sont toujours initialisées.
   ==================================================================== */
(function () {
  "use strict";

  /* ================================================================
     Navigation partagée (désactivable via AUDIT_PAGE_OWNS_NAV)
     ================================================================ */
  function initSharedNav() {
    if (window.AUDIT_PAGE_OWNS_NAV) return;

    /* ---- Navigation : état actif ---- */
    function clearActive() {
      document.querySelectorAll('.nav-item[href], .subitem').forEach(function (n) {
        n.classList.remove('active');
        n.removeAttribute('aria-current');
      });
    }
    document.querySelectorAll('.nav-item[href], .subitem').forEach(function (item) {
      item.addEventListener('click', function () {
        clearActive();
        item.classList.add('active');
        item.setAttribute('aria-current', 'page');
      });
    });

    /* ---- Sous-menu Administration ---- */
    document.querySelectorAll('[data-admin-toggle]').forEach(function (btn) {
      var group = btn.closest('[data-admin-group]');
      var sub = group ? group.querySelector('.submenu') : null;
      if (!sub) return;
      btn.addEventListener('click', function () {
        var open = sub.classList.toggle('open');
        group.classList.toggle('is-open', open);
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });

    /* ---- Listes déroulantes de l'en-tête (Gestion / Session) ---- */
    var dropdowns = Array.prototype.slice.call(document.querySelectorAll('[data-dropdown]'));
    function closeAllDropdowns(except) {
      dropdowns.forEach(function (dd) {
        if (dd === except) return;
        dd.classList.remove('is-open');
        var p = dd.querySelector('[data-dd-panel]');
        var t = dd.querySelector('[data-dd-trigger]');
        if (p) p.classList.remove('open');
        if (t) t.setAttribute('aria-expanded', 'false');
      });
    }
    /* exposé pour les pages qui ont leurs propres composants */
    window.closeAllDropdowns = closeAllDropdowns;

    dropdowns.forEach(function (dd) {
      var trigger = dd.querySelector('[data-dd-trigger]');
      var panel = dd.querySelector('[data-dd-panel]');
      var valueEl = dd.querySelector('[data-dd-value]');
      if (!trigger || !panel) return;
      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        var willOpen = !panel.classList.contains('open');
        closeAllDropdowns(dd);
        panel.classList.toggle('open', willOpen);
        dd.classList.toggle('is-open', willOpen);
        trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      });
      panel.querySelectorAll('[data-dd-option]').forEach(function (opt) {
        opt.addEventListener('click', function () {
          panel.querySelectorAll('[data-dd-option]').forEach(function (o) {
            o.classList.remove('selected');
            o.setAttribute('aria-selected', 'false');
          });
          opt.classList.add('selected');
          opt.setAttribute('aria-selected', 'true');
          if (valueEl) valueEl.textContent = opt.textContent.trim();
          closeAllDropdowns();
        });
      });
    });
    document.addEventListener('click', function () { closeAllDropdowns(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeAllDropdowns();
    });
  }

  /* ================================================================
     Comboboxes — listes déroulantes avec recherche
     Markup (réf. page collecte) :
       <div data-combo data-combo-placeholder="Sélectionner" data-value="">
         <button data-combo-trigger>… <span data-combo-label>…</span></button>
         <div data-combo-panel>
           <div class="combo-search"><svg/><input data-combo-input></div>
           <div data-combo-list>
             <button data-combo-option>Option</button>
           </div>
         </div>
       </div>
     API : window.getComboValue(root) / window.setComboValue(root, val)
     ================================================================ */
  function closeAllCombos(except) {
    document.querySelectorAll('[data-combo-panel].open').forEach(function (cp) {
      var c = cp.closest('[data-combo]');
      if (c === except) return;
      cp.classList.remove('open');
      var t = c ? c.querySelector('[data-combo-trigger]') : null;
      if (t) t.setAttribute('aria-expanded', 'false');
    });
  }

  function initCombos(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-combo]').forEach(function (combo) {
      if (combo.dataset.comboReady) return;
      combo.dataset.comboReady = '1';

      var trigger = combo.querySelector('[data-combo-trigger]');
      var cpanel = combo.querySelector('[data-combo-panel]');
      var input = combo.querySelector('[data-combo-input]');
      var label = combo.querySelector('[data-combo-label]');
      var list = combo.querySelector('[data-combo-list]');
      var options = Array.prototype.slice.call(combo.querySelectorAll('[data-combo-option]'));
      var placeholder = combo.getAttribute('data-combo-placeholder') ||
                        (label ? label.textContent.trim() : '');
      var empty = null;
      if (!trigger || !cpanel) return;

      function closeCombo() {
        cpanel.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
      }
      function openCombo() {
        closeAllCombos(combo);
        cpanel.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
        if (input) { input.value = ''; filterOpts(''); setTimeout(function () { input.focus(); }, 10); }
      }
      function filterOpts(q) {
        q = (q || '').trim().toLowerCase();
        var shown = 0;
        options.forEach(function (o) {
          var ok = o.textContent.toLowerCase().indexOf(q) > -1;
          o.classList.toggle('hidden', !ok);
          if (ok) shown++;
        });
        if (!empty) {
          empty = document.createElement('div');
          empty.className = 'combo-empty';
          empty.textContent = 'Aucun résultat';
          list.appendChild(empty);
        }
        empty.classList.toggle('hidden', shown > 0);
      }
      function selectValue(val) {
        val = val || '';
        if (label) {
          label.textContent = val || placeholder;
          label.classList.toggle('text-muted-2', !val);
          label.classList.toggle('text-ink-2', !!val);
        }
        combo.setAttribute('data-value', val);
        options.forEach(function (o) { o.classList.toggle('selected', o.textContent.trim() === val); });
      }
      /* exposé sur l'élément pour l'API setComboValue */
      combo._comboSelect = selectValue;

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (cpanel.classList.contains('open')) closeCombo(); else openCombo();
      });
      if (input) {
        input.addEventListener('click', function (e) { e.stopPropagation(); });
        input.addEventListener('input', function () { filterOpts(input.value); });
      }
      options.forEach(function (o) {
        o.addEventListener('click', function (e) {
          e.stopPropagation();
          selectValue(o.textContent.trim());
          closeCombo();
        });
      });

      /* valeur initiale éventuelle (data-value au chargement) */
      var initVal = combo.getAttribute('data-value');
      if (initVal) selectValue(initVal);
    });
  }

  /* Fermeture des comboboxes au clic extérieur / Échap (une seule fois) */
  document.addEventListener('click', function () { closeAllCombos(null); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAllCombos(null); });

  /* API publique */
  window.initCombos = initCombos;
  window.getComboValue = function (root) { return root ? (root.getAttribute('data-value') || '') : ''; };
  window.setComboValue = function (root, val) {
    if (!root) return;
    if (root._comboSelect) root._comboSelect(val || '');
    else root.setAttribute('data-value', val || '');
  };



  /* ================================================================
     Pagination unifiée (100 % client) — pilote TOUTE table marquée
     [data-paginate] et sa barre [data-pagination] situées dans le même
     conteneur [data-table-block]. Rendu identique partout (précédent /
     numéros / suivant + compteur « x–y sur N » + sélecteur lignes/page).
     SOURCE UNIQUE de la taille de page : les <option data-pg-size> du
     partial (jamais > 15) ; un plafond dur CAP=15 borne toute valeur.
     Coopère avec la recherche (ne pagine que les lignes visibles, càd
     display !== 'none') et se met à jour sur mutation du <tbody>.
     ================================================================ */
  var PG_CAP = 15;  // plafond dur : jamais plus de 15 lignes par page.
  var PG_ARROW_L = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>';
  var PG_ARROW_R = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>';

  function initPagination(scope) {
    scope = scope || document;
    scope.querySelectorAll('[data-pagination]').forEach(function (bar) {
      if (bar._pgReady) return;
      var block = bar.closest('[data-table-block]') || bar.parentNode;
      var tb = block ? block.querySelector('[data-paginate]') : null;
      if (!tb) return;
      bar._pgReady = true;

      var szTrigger = bar.querySelector('[data-pg-size-trigger]');
      var szPanel = bar.querySelector('[data-pg-size-panel]');
      var szLabel = bar.querySelector('[data-pg-size-label]');
      var szOpts = szPanel ? Array.prototype.slice.call(szPanel.querySelectorAll('[data-pg-size-option]')) : [];
      var info = bar.querySelector('[data-pg-info]');
      var nav = bar.querySelector('[data-pg-nav]');
      var noun = bar.getAttribute('data-noun') || 'éléments';
      var state = { page: 0, size: 15 };
      szOpts.forEach(function (o) { if (o.classList.contains('selected')) state.size = parseInt(o.getAttribute('data-value'), 10) || 15; });

      function dataRows() {
        return Array.prototype.slice.call(tb.children).filter(function (tr) {
          return tr.tagName === 'TR' && !tr.hasAttribute('data-pgskip');
        });
      }
      function pageSize() {
        var v = state.size;
        if (!v || v < 1) v = PG_CAP;
        return Math.min(v, PG_CAP);   // plafond dur
      }
      function mkBtn(html, page, opts) {
        opts = opts || {};
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'page-num'; b.innerHTML = html;
        if (opts.active) { b.classList.add('active'); b.setAttribute('aria-current', 'page'); }
        if (opts.disabled) { b.disabled = true; }
        else { b.addEventListener('click', function () { state.page = page; render(); }); }
        return b;
      }
      function render() {
        var rows = dataRows();
        var vis = rows.filter(function (r) { return r.style.display !== 'none'; });
        var per = pageSize();
        var total = vis.length;
        var pages = Math.max(1, Math.ceil(total / per));
        if (state.page > pages - 1) state.page = pages - 1;
        if (state.page < 0) state.page = 0;
        rows.forEach(function (r) { r.removeAttribute('data-pg'); });
        vis.forEach(function (r, i) { if (Math.floor(i / per) !== state.page) r.setAttribute('data-pg', 'off'); });

        // Masquage fiable (indépendant de Tailwind / attribut hidden) : style inline.
        bar.style.display = (total === 0) ? 'none' : '';
        if (total === 0) return;
        var from = state.page * per + 1, to = Math.min(total, (state.page + 1) * per);
        if (info) {
          info.innerHTML = 'Affichage <b class="text-ink-2 font-bold tabular-nums">' + from + '–' + to +
            '</b> sur <b class="text-brand-600 font-bold tabular-nums">' + total + '</b> ' + noun;
        }
        if (nav) {
          nav.innerHTML = '';
          nav.appendChild(mkBtn(PG_ARROW_L, state.page - 1, { disabled: state.page === 0 }));
          for (var p = 0; p < pages; p++) {
            if (p === 0 || p === pages - 1 || Math.abs(p - state.page) <= 1) {
              nav.appendChild(mkBtn(String(p + 1), p, { active: p === state.page }));
            } else if (Math.abs(p - state.page) === 2) {
              var s = document.createElement('span');
              s.className = 'page-num ell'; s.setAttribute('aria-hidden', 'true'); s.textContent = '…';
              nav.appendChild(s);
            }
          }
          nav.appendChild(mkBtn(PG_ARROW_R, state.page + 1, { disabled: state.page === pages - 1 }));
        }
      }

      /* Menu maison « lignes par page » (ouverture/fermeture/sélection). */
      if (szTrigger && szPanel) {
        function szClose() { szPanel.classList.remove('open'); szTrigger.setAttribute('aria-expanded', 'false'); }
        szTrigger.addEventListener('click', function (e) {
          e.stopPropagation();
          var willOpen = !szPanel.classList.contains('open');
          szPanel.classList.toggle('open', willOpen);
          szTrigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        });
        szOpts.forEach(function (o) {
          o.addEventListener('click', function (e) {
            e.stopPropagation();
            state.size = parseInt(o.getAttribute('data-value'), 10) || 15;
            szOpts.forEach(function (x) { x.classList.remove('selected'); x.setAttribute('aria-selected', 'false'); });
            o.classList.add('selected'); o.setAttribute('aria-selected', 'true');
            if (szLabel) szLabel.textContent = o.textContent.trim();
            szClose(); state.page = 0; render();
          });
        });
        document.addEventListener('click', szClose);
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') szClose(); });
      }
      tb._pgRender = render;
      new MutationObserver(function () { render(); }).observe(tb, { childList: true });
      render();
    });

    /* Recalcule toutes les tables paginées quand une recherche filtre les lignes
       (les handlers de recherche posent display:none ; on recompte APRÈS eux) ou
       au changement d'onglet. */
    if (!initPagination._hooked) {
      initPagination._hooked = true;
      var refreshAll = function () {
        setTimeout(function () {
          document.querySelectorAll('[data-paginate]').forEach(function (tb) {
            if (tb._pgRender) tb._pgRender();
          });
        }, 0);
      };
      /* Toute frappe dans un champ (recherche, filtre…) peut masquer des lignes
         via display:none ; on recompte après les handlers de recherche. Large à
         dessein pour couvrir toutes les recherches quel que soit leur attribut. */
      document.addEventListener('input', function (e) {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT')) refreshAll();
      });
      document.addEventListener('click', function (e) {
        if (e.target.closest('[data-tab]')) refreshAll();
      });
    }
  }
  window.initPagination = initPagination;

  /* ================================================================
     Démarrage
     ================================================================ */
  function boot() {
    initSharedNav();
    initCombos(document);
    initPagination(document);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
