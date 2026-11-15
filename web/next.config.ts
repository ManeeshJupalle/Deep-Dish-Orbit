import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Plain static files in out/, served by Azure Static Web Apps. Pages fetch the API in the browser,
  // so Cache Components / partial prerendering (which static export does not allow) are not used.
  output: "export",
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
