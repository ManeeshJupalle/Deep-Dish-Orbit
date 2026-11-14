import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Phase 1 placeholder. The Ask screen is built in Phase 5.
export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle>FlameCheck</CardTitle>
          <CardDescription>
            Fire-safety answers from NASA microgravity combustion data, with a citation for every claim.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Ask screen coming in Phase 5.</CardContent>
      </Card>
    </main>
  );
}
