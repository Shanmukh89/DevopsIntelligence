import React from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import DashboardView from "@/components/dashboard/dashboard-view";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  // Fetch the user's profile to determine auth provider
  const { data: profile } = await supabase
    .from("profiles")
    .select("auth_provider")
    .eq("id", user.id)
    .single();

  const authProvider = profile?.auth_provider || null;

  // Check if user has a GitHub App installation (replaces old OAuth identity check)
  const { data: installation } = await supabase
    .from("github_installations")
    .select("id")
    .eq("profile_id", user.id)
    .single();

  const hasInstallation = !!installation;

  // 1. Fetch repositories
  const { data: repositories } = await supabase
    .from("repositories")
    .select("*")
    .order("created_at", { ascending: false });

  // 2. Fetch Pull Requests
  const { data: pullRequests } = await supabase
    .from("pull_requests")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(10);

  // 3. Fetch Builds
  const { data: builds } = await supabase
    .from("builds")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(10);

  // 4. Fetch Vulnerabilities
  const { data: vulnerabilities } = await supabase
    .from("vulnerabilities")
    .select("*")
    .order("created_at", { ascending: false });

  // 5. Fetch Costs
  const { data: costs } = await supabase
    .from("cloud_costs")
    .select("*")
    .order("created_at", { ascending: false });

  const anomalyTimeline: any[] = [];

  return (
    <DashboardView
      repositories={repositories || []}
      pullRequests={pullRequests || []}
      builds={builds || []}
      vulnerabilities={vulnerabilities || []}
      costs={costs || []}
      hasInstallation={hasInstallation}
      authProvider={authProvider}
      anomalyTimeline={anomalyTimeline}
    />
  );
}
