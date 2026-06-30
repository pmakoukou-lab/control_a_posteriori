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
     Démarrage
     ================================================================ */
  function boot() {
    initSharedNav();
    initCombos(document);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
