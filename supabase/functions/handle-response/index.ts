// Edge Function: handle-response
// Permite responder a actividades desde email/celular sin autenticación.
// Valida un token temporal y actualiza el estado de la actividad.

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

function htmlPage(title: string, body: string): Response {
  const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} — PG Machine</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; background: #f8fafc; padding: 16px; }
    .container { max-width: 500px; margin: 0 auto; }
    .card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .header { background: #1e293b; color: white; padding: 20px; text-align: center; }
    .header h1 { font-size: 1.3rem; font-weight: 700; }
    .body { padding: 20px; }
    .info { background: #f1f5f9; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
    .info-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9rem; }
    .info-label { color: #64748b; }
    .info-value { font-weight: 600; color: #1e293b; }
    textarea { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 1rem; min-height: 120px; resize: vertical; font-family: inherit; }
    button { width: 100%; background: #16a34a; color: white; border: none; border-radius: 8px; padding: 14px; font-size: 1.1rem; font-weight: 700; cursor: pointer; margin-top: 12px; }
    button:hover { background: #15803d; }
    .success { background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 20px; text-align: center; }
    .success h2 { color: #16a34a; margin-bottom: 8px; }
    .error { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 20px; text-align: center; }
    .error h2 { color: #ef4444; margin-bottom: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header"><h1>${title}</h1></div>
      <div class="body">${body}</div>
    </div>
  </div>
</body>
</html>`;
  return new Response(html, {
    headers: { ...corsHeaders, "Content-Type": "text/html; charset=utf-8" },
  });
}

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  const url = new URL(req.url);
  const token = url.searchParams.get("token");

  if (!token) {
    return htmlPage("Error", `<div class="error"><h2>Enlace inválido</h2><p>No se proporcionó un token de respuesta.</p></div>`);
  }

  // Buscar actividad por token
  const { data: activity, error } = await supabase
    .from("activities")
    .select("*, opportunity:opportunity_id(proyecto, cuenta)")
    .eq("response_token", token)
    .maybeSingle();

  if (error || !activity) {
    return htmlPage("Error", `<div class="error"><h2>Token inválido</h2><p>Este enlace no es válido o ya fue utilizado.</p></div>`);
  }

  // Verificar expiración
  if (activity.token_expires_at && new Date(activity.token_expires_at) < new Date()) {
    return htmlPage("Error", `<div class="error"><h2>Enlace expirado</h2><p>Este enlace ha expirado. Contacta al equipo para más información.</p></div>`);
  }

  // GET: mostrar formulario
  if (req.method === "GET") {
    const opp = activity.opportunity || {};
    const formBody = `
      <div class="info">
        <div class="info-row"><span class="info-label">Cuenta</span><span class="info-value">${opp.cuenta || ""}</span></div>
        <div class="info-row"><span class="info-label">Proyecto</span><span class="info-value">${opp.proyecto || ""}</span></div>
        <div class="info-row"><span class="info-label">Tipo</span><span class="info-value">${activity.tipo || ""}</span></div>
        <div class="info-row"><span class="info-label">Objetivo</span><span class="info-value">${activity.objetivo || ""}</span></div>
        <div class="info-row"><span class="info-label">Destinatario</span><span class="info-value">${activity.destinatario || ""}</span></div>
      </div>
      <form method="POST" action="?token=${token}">
        <label style="font-weight:600; display:block; margin-bottom:8px;">Feedback / Respuesta:</label>
        <textarea name="feedback" placeholder="Escribe tu respuesta aquí..." required></textarea>
        <button type="submit">Confirmar Respuesta</button>
      </form>
    `;
    return htmlPage("Responder Actividad", formBody);
  }

  // POST: procesar respuesta
  if (req.method === "POST") {
    let feedback = "";
    const contentType = req.headers.get("content-type") || "";

    if (contentType.includes("application/x-www-form-urlencoded")) {
      const formData = await req.text();
      const params = new URLSearchParams(formData);
      feedback = params.get("feedback") || "";
    } else if (contentType.includes("application/json")) {
      const json = await req.json();
      feedback = json.feedback || "";
    }

    if (!feedback.trim()) {
      return htmlPage("Error", `<div class="error"><h2>Feedback requerido</h2><p>Por favor escribe una respuesta.</p></div>`);
    }

    // Actualizar actividad
    const { error: updateError } = await supabase
      .from("activities")
      .update({
        estado: "Respondida",
        feedback: feedback.trim(),
        response_token: null,
        token_expires_at: null,
      })
      .eq("id", activity.id);

    if (updateError) {
      return htmlPage("Error", `<div class="error"><h2>Error</h2><p>No se pudo guardar la respuesta. Intenta de nuevo.</p></div>`);
    }

    return htmlPage("Respuesta Enviada", `
      <div class="success">
        <h2>Respuesta registrada</h2>
        <p style="margin-top:8px; color:#475569;">Tu feedback ha sido guardado exitosamente. El equipo será notificado.</p>
      </div>
    `);
  }

  return htmlPage("Error", `<div class="error"><h2>Método no soportado</h2></div>`);
});
