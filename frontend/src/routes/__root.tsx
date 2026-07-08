import { createRootRouteWithContext, Outlet, ScrollRestoration, HeadContent, Scripts } from "@tanstack/react-router";
import * as React from "react";
import type { QueryClient } from "@tanstack/react-query";
import "@/styles.css";

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  head: () => ({
    meta: [
      {
        charSet: "utf-8",
      },
      {
        name: "viewport",
        content: "width=device-width, initial-scale=1",
      },
      {
        title: "Insurance DV",
      },
    ]
  }),
  component: RootComponent,
});

function RootComponent() {
  return (
    <html lang="fr">
      <head>
        <HeadContent />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}
