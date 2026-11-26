import nextCoreWebVitals from "eslint-config-next/core-web-vitals"
import nextTypescript from "eslint-config-next/typescript"

const eslintConfig = [
    ...nextCoreWebVitals,
    ...nextTypescript,
    {
        ignores: [".next/**", "node_modules/**", "coverage/**", "next-env.d.ts"],
    },
    {
        rules: {
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/no-unused-vars": [
                "error",
                { argsIgnorePattern: "^_" },
            ],
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/explicit-module-boundary-types": "off",
            "no-console": "warn",
        },
    },
]

export default eslintConfig
