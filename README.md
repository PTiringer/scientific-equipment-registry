# Scientific Equipment Registry

A NOMAD Oasis plugin for NOMAD 1.4.1 and later with an equipment ELN schema and a dedicated Explore app. Each NOMAD entry represents one item. The app appears beside Scientific Staff in the CBS group. Its dashboard provides quick filters for equipment name, department, category, and status. The sidebar also provides equipment ID, location, equipment group, and visibility filters.

## Install in NOMAD Oasis

Install this package in the Python environment that runs NOMAD. From the root of the extracted package, run:

```sh
python -m pip install --no-deps .
```

For a container deployment, add the package to the NOMAD image build so the app and worker both use the same plugin version. Rebuild and restart them on the test Oasis first. If the deployment explicitly restricts enabled plugins, add these entry points to its existing `plugins.include` list:

```text
nomad_equipment_registry:equipment_schema
nomad_equipment_registry.app:equipment_app
```

Create an entry from the **Equipment record** template in a NOMAD upload, or upload `examples/example-equipment.archive.yaml` to try the registry. Open **Explore → CBS → Scientific Equipment Registry** and use **Filters → Visibility** to select a scope that includes your test upload. NOMAD's upload permissions govern access to each record. For an internal registry, keep uploads unpublished and share them with the intended users or groups.

## Maintain records

- Use an institution-assigned equipment ID. The registry administrator must ensure IDs are unique and keep them stable. This version leaves enforcement of uniqueness and immutability to the institution.
- Department and location are text fields. Use consistent spelling to keep each department or location under a single filter value.
- Owners and contacts are selected from NOMAD user accounts. Current owner is maintained independently of the primary ownership history.
- To transfer primary responsibility, enter the old assignment's last day and add a new assignment with its start day, project description, and recorded-on timestamp. The top-level **Primary owner** is populated from the single open assignment. Leave the end date blank for that assignment only. Dates are treated as inclusive.
- Missing required values, overlapping or reversed ownership periods, multiple open assignments, and incomplete contacts generate processing warnings. NOMAD can still save incomplete drafts. Recorded on is an editable timestamp rather than an audit log.

## Smoke check on test Oasis

1. Create or upload the example record. Confirm the Explore app shows the row and that the status and category filters find it.
2. Select a NOMAD user and fill in a primary ownership period. Save and verify the top-level primary owner in the entry data.
3. Close the period and create a new open period with a different owner. Save and verify the owner changes and both periods remain visible.
4. Verify that another intended registry user can see the record after the upload is shared.

## Test on the existing NOMAD 1.4 deployment

Run these commands on `test-nomad` from the active Docker Compose directory, with
the same project and Compose files you normally use. Extract the plugin ZIP
somewhere outside that directory and set `registry_src` to its extracted
`scientific-equipment-registry` folder.

```bash
registry_src=/absolute/path/to/scientific-equipment-registry
app_id=$(docker compose ps -q app)
docker compose exec -T app python -c \
  "from importlib.metadata import version; print(version('nomad-lab'))"

base_id=$(docker inspect --format '{{.Image}}' "$app_id")
base_user=$(docker image inspect --format '{{.Config.User}}' "$base_id")
docker image tag "$base_id" nomad-oasis-local:equipment-test-base

docker build -t nomad-oasis-local:equipment-test \
  --build-arg "BASE_USER=${base_user:-root}" -f - "$registry_src" <<'DOCKERFILE'
FROM nomad-oasis-local:equipment-test-base
ARG BASE_USER=root
USER root
COPY pyproject.toml /tmp/equipment-plugin/
COPY src /tmp/equipment-plugin/src
RUN if command -v uv >/dev/null 2>&1; then \
      uv pip install --python "$(command -v python)" --no-deps /tmp/equipment-plugin; \
    else \
      python -m pip install --no-deps /tmp/equipment-plugin; \
    fi && rm -rf /tmp/equipment-plugin
USER ${BASE_USER}
DOCKERFILE
```

After a successful build, verify the plugin loads in the new image:

```bash
docker run --rm --entrypoint python nomad-oasis-local:equipment-test -c \
  'from nomad_equipment_registry import equipment_schema; from nomad_equipment_registry.app import equipment_app; equipment_schema.load(); print(equipment_app.app.label)'
```

If your deployment has a plugin allowlist, add the two entry points listed
above before restarting the services. Apply the test image to the existing
app and worker, then check their logs and reload the proxy once the app is healthy:

```bash
NOMAD_IMAGE=nomad-oasis-local:equipment-test \
  docker compose up -d --no-deps app worker
docker compose ps app worker
docker compose logs --tail=80 app worker
docker compose exec -T proxy nginx -s reload
```

Roll back by substituting `nomad-oasis-local:equipment-test-base` for the test
image in the same Compose command and reloading the proxy again. For permanent
integration, add the plugin to the same image build step as the Scientific Staff
Database. The test image uses the currently running NOMAD release.
