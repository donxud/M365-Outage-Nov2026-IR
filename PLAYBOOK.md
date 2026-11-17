# Playbook: Major Microsoft 365 / SaaS Provider Outage

> Security teams: see also [SECURITY-RESILIENCE.md](SECURITY-RESILIENCE.md) for the defense-in-depth view.

**Scope:** a provider-side outage that takes down email, collaboration or security tooling you rely on. You cannot fix the provider; your job is to detect fast, keep the business and security operations running, stop attackers exploiting the confusion, and recover cleanly.

**Severity trigger:** two or more core services (mail, chat, identity, EDR/XDR console) degraded for 30 minutes or more, or any outage of your incident communication channel.

| Phase | Goal | Owner (fill in) |
|---|---|---|
| 0. Prepare | Have the fallbacks ready before you need them | Security + IT ops |
| 1. Detect and confirm | Know before users call; confirm it is the provider, not you | SOC / NOC |
| 2. Communicate | One source of truth, through a channel that still works | Incident commander |
| 3. Operate degraded | Keep critical work and security monitoring going | IT ops + SOC |
| 4. Guard against exploitation | Block outage-themed phishing and fake "fixes" | SOC |
| 5. Recover | Bring things back in order and catch up on what was missed | IT ops + SOC |
| 6. Review | Turn it into improvements | Incident commander |

---

## Phase 0 — Prepare (do this now)

- [ ] **Out-of-band channel** that does not depend on the provider: e.g. Signal/WhatsApp group, a phone bridge, or a status page on separate hosting. Test it quarterly.
- [ ] **Offline contact list** for the IR team, leadership, IT owners and key vendors (phone numbers, not just email).
- [ ] **Provider health monitoring** that does not wait for user tickets: Microsoft Graph service health polling (see `tools/m365_health_watch.py`) feeding your SIEM, Tines, or pager.
- [ ] **Know which security tools share the provider.** If Defender XDR is down, what still sees endpoints and email? (Firewall logs, EDR local logs, proxy/DNS, a non-Microsoft SIEM path.)
- [ ] **Break-glass admin accounts** excluded from conditional-access dependencies that could fail, stored and tested per your policy.
- [ ] **Pre-approved change freeze** wording for provider outages, so nobody "fixes" your tenant while the provider is broken.
- [ ] **Pre-written user advisory** (see `templates/user-advisory.md`).

## Phase 1 — Detect and confirm

1. Check the **Microsoft 365 admin center → Service health** (or Graph API) for an active incident. Record the incident IDs (e.g. EX…, MO…, TM…).
2. Confirm it is **not local**: test from an outside network; check your own DNS, proxy, firewall and identity provider.
3. Open an internal incident ticket, linking the provider incident IDs. Note the start time in UTC.
4. **Freeze changes** to mail flow, connectors, conditional access and DNS. Provider outages tempt admins into risky changes that outlive the outage.

## Phase 2 — Communicate

1. Move the IR team to the **out-of-band channel**.
2. Name one incident commander and one communicator.
3. Send the **user advisory** through whatever still works (SMS, intranet on separate hosting, signage, managers). Include the phishing warning from the start.
4. Update leadership on a fixed cadence (e.g. every 2 hours): impact, workaround, provider status, next update time.
5. Label provider statements as **preliminary**. Early updates during this outage pointed at health checks and a network rollback; the preliminary PIR named a different cause.

## Phase 3 — Operate degraded

- **Mail:** inbound mail usually queues at the sender and is retried; Microsoft also extended its delivery window. Tell users mail is delayed, not lost. For critical external contacts, agree on phone as a fallback.
- **Collaboration:** move urgent meetings to a phone bridge or an alternate platform the business has approved.
- **Security monitoring:** if the XDR console is down, fall back to:
  - firewall, proxy and DNS logs for outbound anomalies;
  - local EDR logs or the vendor's alternate console;
  - your SIEM, if ingestion still works (check — see `queries/kql/siem_ingestion_gaps.kql`).
- **Record what you could not see**, with time windows, for Phase 5.

## Phase 4 — Guard against exploitation

During this outage, Microsoft Threat Intelligence reported phishing emails that **referenced the real incident ID EX1550543**.

- [ ] Warn users: no legitimate fix requires them to enter a password, install software, or call a number from an email.
- [ ] Hunt for outage-themed lures: `queries/kql/outage_phishing_lures.kql`.
- [ ] Block confirmed lure senders, domains and URLs; purge delivered messages.
- [ ] Watch the help desk for social engineering ("I'm locked out because of the outage, reset my MFA").
- [ ] Verify any "Microsoft support" contact through the admin center, never through a link or number in an email.

## Phase 5 — Recover

1. Confirm recovery in Service health **and** with your own tests (send/receive, Teams, SharePoint, XDR console).
2. Lift the change freeze deliberately; review any emergency changes made during the outage and roll back what is no longer needed.
3. **Catch up on security visibility:** run `siem_ingestion_gaps.kql` for the outage window, then re-run critical detections over that window once delayed data arrives.
4. Check for sign-in anomalies after recovery (`post_outage_signin_anomalies.kql`): credential phishing during the outage shows up as unusual successful sign-ins afterward.
5. Tell users when service is back and repeat the phishing warning; lures often continue after recovery.

## Phase 6 — Review (within 5 business days, then again after the provider's final PIR)

- [ ] Timeline of **your** detection, decisions and communications vs the provider's timeline. How long until you knew?
- [ ] Did the out-of-band channel and contact list work?
- [ ] Which security controls went blind, for how long, and what covered the gap?
- [ ] Phishing: how many lures arrived, how many were reported, clicked, or led to sign-ins?
- [ ] Concentration risk: which critical functions depend on a single provider? Record accepted risks and mitigations.
- [ ] Update this playbook and schedule a tabletop exercise.
