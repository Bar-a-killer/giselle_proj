import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // This rule flags the standard "setLoading(true) -> await fetch -> setData/setLoading(false)"
      // pattern used throughout app/*/page.tsx for client-side data fetching. That pattern is
      // correct here (no Suspense/Server Components data layer in this prototype), so disable it
      // instead of contorting straightforward fetch-on-mount effects.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
