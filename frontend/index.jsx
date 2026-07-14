/* Postgres tool plugin — frontend descriptor (mirrors PiKaOs-Plugin-Knowledge/frontend/index.jsx's
   shape). This plugin's frontend footprint is just the DB-choice bootstrap screen (Step 1 of install,
   relocated from Core here in R2) — it owns no sidebar route, so there's no `routes`/`nav` list.

   `bootstrapScreens` is the generic seam Core's plugins/index.jsx exposes for the pre-login/pre-app
   install window (`resolveShellMode()` in shell-mode.js decides WHEN a stage like 'db-choice' is
   active; this plugin only supplies WHAT renders once it is — any plugin can claim a bootstrap stage
   the same way, Core never special-cases 'postgres'). */
import React from 'react';

import { DbChoice } from './DbChoice.jsx';

export default {
  id: 'postgres',
  bootstrapScreens: {
    'db-choice': (ctx) => <DbChoice t={ctx.t} language={ctx.language} onLang={ctx.onLang} />,
  },
};
