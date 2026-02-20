// Edge Function: calendar-sync
// Recibe eventos de calendario desde Power Automate y los guarda en calendar_inbox.
// Auth: Bearer token via CALENDAR_SYNC_API_KEY secret.

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const API_KEY = Deno.env.get("CALENDAR_SYNC_API_KEY") || "";

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function jsonResponse(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Método no soportado" }, 405);
  }

  // Validar API key
  const authHeader = req.headers.get("Authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (!API_KEY || token !== API_KEY) {
    return jsonResponse({ error: "No autorizado" }, 401);
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "JSON inválido" }, 400);
  }

  const userEmail = (body.user_email as string || "").trim().toLowerCase();
  if (!userEmail) {
    return jsonResponse({ error: "user_email es requerido" }, 400);
  }

  // Buscar usuario por email en profiles
  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("id, team_id")
    .eq("email", userEmail)
    .maybeSingle();

  if (profileError || !profile) {
    return jsonResponse({ error: `Usuario no encontrado: ${userEmail}` }, 404);
  }

  const outlookEventId = (body.outlook_event_id as string || "").trim();

  // Deduplicar por outlook_event_id
  if (outlookEventId) {
    const { data: existing } = await supabase
      .from("calendar_inbox")
      .select("id")
      .eq("outlook_event_id", outlookEventId)
      .eq("profile_id", profile.id)
      .maybeSingle();

    if (existing) {
      return jsonResponse({ status: "duplicate", inbox_id: existing.id });
    }
  }

  // Normalizar attendees: acepta array o string separado por ;
  let attendees: string[] = [];
  const rawAttendees = body.attendees;
  if (Array.isArray(rawAttendees)) {
    attendees = rawAttendees.map((a: unknown) => String(a).trim()).filter(Boolean);
  } else if (typeof rawAttendees === "string" && rawAttendees.trim()) {
    attendees = rawAttendees.split(";").map((a: string) => a.trim()).filter(Boolean);
  }

  // Insertar en calendar_inbox
  const record = {
    team_id: profile.team_id,
    profile_id: profile.id,
    user_email: userEmail,
    subject: (body.subject as string || "").trim(),
    start_time: body.start || null,
    end_time: body.end || null,
    organizer: (body.organizer as string || "").trim(),
    attendees: attendees,
    location: (body.location as string || "").trim(),
    body: (body.body as string || "").trim(),
    outlook_event_id: outlookEventId || null,
    status: "pending",
  };

  const { data: inserted, error: insertError } = await supabase
    .from("calendar_inbox")
    .insert(record)
    .select("id")
    .single();

  if (insertError) {
    return jsonResponse({ error: "Error al guardar", detail: insertError.message }, 500);
  }

  return jsonResponse({ status: "ok", inbox_id: inserted.id });
});
