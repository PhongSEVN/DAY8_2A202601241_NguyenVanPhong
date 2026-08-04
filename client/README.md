## Chạy full stack (backend + client)

Backend FastAPI (`server.py` ở project root) đã wire sẵn vào Task 9/10, expose
`POST /query`. Vite proxy `/api/*` -> `http://localhost:8001/*` (xem `vite.config.ts`).

```bash
# Terminal 1 — backend, chạy từ project root (không cd vào client/)
uvicorn server:app --reload --port 8001

# Terminal 2 — client
cd client
npm install
npm run dev
```

Trước khi Task 9/10 xong, `/query` trả về answer mockup báo "pipeline chưa
implement" thay vì lỗi — UI vẫn test được luôn không cần chờ backend hoàn chỉnh.

TODO còn lại (Role 4 — Vũ Huy Hoàng):
- `server.py`: nối `req.conversation_history` vào `generate_with_citation()` để có
  multi-turn memory thật (hiện field này nhận nhưng chưa dùng).
- Copy UI đã đổi từ theme "Trợ lý Pháp lý" (project cũ) sang University Services
  (title, brand name, placeholder, starter questions, icon `gavel` → `school`/
  `description`) — review lại text/màu sắc cho khớp branding trường nếu cần.

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
