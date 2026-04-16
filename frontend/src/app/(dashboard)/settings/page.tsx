import React from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import SettingsView from "@/components/dashboard/settings-client-view";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/signin");

  // Fetch the user's profile for auth provider info
  const { data: profile } = await supabase
    .from("profiles")
    .select("auth_provider")
    .eq("id", user.id)
    .single();

  const authProvider = profile?.auth_provider || null;

  // Fetch the GitHub App installation for this user
  const { data: installation } = await supabase
    .from("github_installations")
    .select("*")
    .eq("profile_id", user.id)
    .single();

  // Count active repos linked to the installation
  let repoCount = 0;
  if (installation) {
    const { count } = await supabase
      .from("repositories")
      .select("*", { count: "exact", head: true })
      .eq("installation_id", installation.id)
      .eq("is_active", true);
    repoCount = count || 0;
  }

  return (
    <SettingsView
      user={user}
      installation={installation}
      repoCount={repoCount}
      authProvider={authProvider}
    />
  );
}
