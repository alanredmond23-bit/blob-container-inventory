---
name: azure-billing-connect
description: "Connect apps to Azure for cost, usage, and billing data (Cost Management + Billing REST), plus auth/RBAC and realistic limits for a custom billing UI. Use when building dashboards, exports, invoices, budgets, or planning payment flows outside the Azure portal."
---

# Azure billing & cost connectivity (custom UI / portal)

This skill summarizes **Microsoft’s official surface area** for pulling **cost, usage, and billing** data into your own application, and what is (and is not) realistic for **“real-time”** reporting or **pay-from-your-UI** flows.

Always confirm behavior for **your** agreement type: **Pay-as-you-go**, **Microsoft Customer Agreement (MCA)**, **Enterprise Agreement (EA)**, **CSP / Partner**, etc. Scopes and APIs differ.

---

## Research summary (what Azure actually offers)

### Cost & usage (Cost Management — `Microsoft.CostManagement`)

| Capability | Typical use in a custom UI | Primary API pattern |
|------------|----------------------------|---------------------|
| Aggregated cost / usage | Dashboards, rollups by RG, service, tag, day | **`POST {scope}/providers/Microsoft.CostManagement/query`** — see [Query - Usage](https://learn.microsoft.com/en-us/rest/api/cost-management/query/usage) (e.g. api-version `2025-03-01`) |
| Large / recurring raw cost files | Data warehouse, FinOps, “at scale” ingestion | **Exports** to storage — [Exports REST](https://learn.microsoft.com/en-us/rest/api/cost-management/exports), [ingest at scale](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/ingest-azure-usage-at-scale) |
| Line-item style detail | CSV pipelines, reconciliation | **Cost Details / export** patterns (async reports); see Cost Management docs on **usage details** and **exports** (same family as exports / cost details APIs) |
| Guardrails | Budget burn-down, alerts | **Budgets** API under Cost Management; wire alerts to your notification system |

**Scopes** (from [Query - Usage](https://learn.microsoft.com/en-us/rest/api/cost-management/query/usage)): subscription, resource group, management group, billing account, billing profile, invoice section, partner customer, EA department / enrollment account, etc. Your app must use a scope the signed-in identity can access.

### Invoices & billing accounts (Billing — `Microsoft.Billing`)

| Capability | Typical use | Notes |
|------------|-------------|--------|
| List / get invoices, download PDFs / documents | “Billing” tab in your portal | [Azure Billing REST](https://learn.microsoft.com/en-us/rest/api/billing/), e.g. [Invoices](https://learn.microsoft.com/en-us/rest/api/billing/invoices) |
| Transactions on an invoice | Line-level billing ledger | e.g. [Transactions - List By Invoice](https://learn.microsoft.com/en-us/rest/api/billing/transactions/list-by-invoice) |
| Payment terms validation (MCA-style) | Eligibility checks before changing terms | e.g. [Validate Payment Terms](https://learn.microsoft.com/en-us/rest/api/billing/billing-accounts/validate-payment-terms) |

**Payment from a fully custom UI:** Public docs emphasize **reading** invoices and **managing payment instruments / terms** in product flows; a **one-click “charge this card now”** API that replaces **all** Microsoft-hosted payment UX is often **not** documented as a single public REST call for every billing type. Plan for: **invoice download**, **balance due display**, **deep link** to Microsoft-hosted payment where required, and **legal/compliance** review for storing or tokenizing payment data (usually you **do not** — you integrate with Microsoft’s Commerce flows or invoicing).

---

## Authentication & authorization (production)

- **Plane:** These APIs are **Azure Resource Manager (management plane)** calls to `https://management.azure.com/...` with **Microsoft Entra ID** tokens (OAuth2).
- **Typical identities:** user delegated auth, or a **backend service** using a **service principal** (client credentials) with narrowly scoped RBAC.
- **Roles (examples — use least privilege):**
  - **Cost data:** [Cost Management Reader](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#cost-management-reader) (or Contributor where you must create exports/budgets).
  - **Billing / invoices:** often **Billing account reader** / agreements-specific roles — see Microsoft docs for **your** billing setup.
- **Never** ship subscription keys or broad Owner unless required; scope to the **management group**, **subscription**, or **billing scope** you display in the UI.

SDK options (pick one stack and stick to it):

- **REST +** `DefaultAzureCredential` / MSAL (any language).
- **.NET:** Azure.ResourceManager.CostManagement, Azure.ResourceManager.* Billing* packages (track current SDK names on Learn).
- **Python:** Azure SDK management clients for Cost Management / Billing (check package names and API versions on [Python Azure SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/mgmt-costmanagement-readme)).

---

## “Real-time” expectations (set with stakeholders)

Azure cost data is **not** generally **per-minute live** like application metrics:

- Usage must be **processed** and **rated** before it appears in Cost Management; many teams see **hours to ~24–48h** lag depending on service, meter, and agreement (confirm in current Microsoft **understand cost data** / latency documentation).
- **Query API** is excellent for **near-current** rollups (e.g. month-to-date, daily grain); it is **not** a substitute for **Azure Monitor** if you need **live resource metrics** (CPU, requests, etc.).

**Practical UI pattern:** show **“last refreshed”** timestamps, offer **granularity** (daily / hourly where supported), and optionally blend **Monitor metrics** for **live ops** with **Cost Management** for **money**.

---

## Suggested architecture for your custom portal

```text
[ Browser UI ] → [ Your API backend ] → ARM: Microsoft.CostManagement (query, exports, budgets)
                              ↘        → ARM: Microsoft.Billing (invoices, accounts)
                              ↘        → (optional) Microsoft.Consumption / other RP per scenario
Identity: Entra ID app registration → RBAC on scopes your customers need
Secrets: Key Vault, managed identity on backend; no keys in the SPA
```

**Exports** path: schedule Cost Management **export** to a **storage account** your backend controls → your UI reads **curated aggregates** from your DB fed by those files (good for heavy historical reporting).

---

## Implementation checklist

1. Identify **billing type** (MCA / EA / PAYG / CSP) and **scopes** (billing account ID, billing profile, subscriptions, management groups).
2. Register an **Entra app**; implement **auth** to your API; grant **least-privilege RBAC** on those scopes.
3. Prototype **`query`** for month-to-date cost by **ResourceGroup** or **ServiceName**; paginate using **`nextLink`** when present.
4. Add **exports** if you need **full detail** or **FOCUS**-style datasets.
5. Add **Billing** reads for **invoice list + PDF URLs** if your UI needs true “billing documents”.
6. For **payments**, define UX with your finance team: **deep link** vs **hosted payment** vs **invoice-only** (wire/check).

---

## Official entry points (bookmark)

- [Query - Usage (REST)](https://learn.microsoft.com/en-us/rest/api/cost-management/query/usage) — core dashboard queries.
- [Cost Management — exports](https://learn.microsoft.com/en-us/rest/api/cost-management/exports) — recurring cost files.
- [Ingest Azure usage at scale](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/ingest-azure-usage-at-scale) — enterprise patterns.
- [Azure Billing REST](https://learn.microsoft.com/en-us/rest/api/billing/) — invoices and billing accounts.
- [Review subscription billing via REST](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/review-subscription-billing) — worked examples.

---

## When to use other tools

- **Live operational metrics** (not cost): Azure Monitor, AMPLS, Application Insights — different APIs.
- **Solely “what will we spend next month”**: Cost Management **forecast** APIs / docs (verify current API version on Learn) — blend with finance-owned assumptions.

---

*Last research pass for this skill: Microsoft Learn Cost Management Query API (`2025-03-01`) and Billing REST overview; validate api-versions before shipping code.*
