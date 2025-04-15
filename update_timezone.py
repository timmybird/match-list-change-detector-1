#!/usr/bin/env python3
"""
Utility script to update timezone settings across multiple projects.

Scans Docker Compose files and updates timezone environment variables.
"""

import os
import re

# List of projects to update
PROJECTS = [
    "../FogisCalendarPhoneBookSync",
    "../MatchListProcessor",
    "../TeamLogoCombiner",
    "../fogis_api_client_python",
    "../google-drive-service",
]

# Timezone to set
TIMEZONE = "Europe/Stockholm"


def update_docker_compose(file_path):
    """Update a docker-compose.yml file to include the timezone setting."""
    print(f"Updating {file_path}...")

    # Read the file
    with open(file_path, "r") as f:
        content = f.read()

    # Check if the file already has TZ setting
    if f"TZ={TIMEZONE}" in content:
        print(f"  Already has timezone setting.")
        return False

    # Find all service definitions
    services = re.findall(r"(\s+\w+:\s*\n(?:\s+[^\n]+\n)+)", content)

    if not services:
        print(f"  No services found in {file_path}")
        return False

    # Track if we made any changes
    made_changes = False

    # For each service, add the timezone if it doesn't have it
    for service in services:
        # Check if the service already has environment section
        env_match = re.search(r"(\s+environment:\s*\n(?:\s+-\s+[^\n]+\n)*)", service)

        if env_match:
            # Has environment section, check if it has TZ
            env_section = env_match.group(1)
            if f"TZ={TIMEZONE}" not in env_section:
                # Add TZ to existing environment section
                indent_match = re.search(r"(\s+)-", env_section)
                if indent_match:
                    indent = indent_match.group(1)
                else:
                    # If no existing environment variables, use the indentation from the
                    # environment line
                    env_line_match = re.search(r"(\s+)environment:", env_section)
                    if env_line_match:
                        indent = env_line_match.group(1) + "  "
                    else:
                        indent = "      "  # Default indentation

                new_env_section = env_section + f"{indent}- TZ={TIMEZONE}\n"
                content = content.replace(env_section, new_env_section)
                made_changes = True
        else:
            # No environment section, add one
            # Find the indentation level
            indent_match = re.search(r"(\s+)\w+:", service)
            if indent_match:
                indent = indent_match.group(1)
                # Find where to insert the environment section
                lines = service.split("\n")
                new_lines = []
                inserted = False

                for line in lines:
                    new_lines.append(line)
                    if re.match(r"\s+\w+:", line) and not inserted:
                        # Insert after the service name
                        new_lines.append(f"{indent}  environment:")
                        new_lines.append(f"{indent}    - TZ={TIMEZONE}")
                        inserted = True
                        made_changes = True

                if inserted:
                    new_service = "\n".join(new_lines)
                    content = content.replace(service, new_service)

    if made_changes:
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(content)
        print(f"  Updated successfully.")
        return True
    else:
        print(f"  No changes needed.")
        return False


def update_env_template(project_dir):
    """Update .env.template file to include the timezone setting."""
    env_template = os.path.join(project_dir, ".env.template")

    if not os.path.exists(env_template):
        print(f"No .env.template found in {project_dir}")
        return False

    print(f"Updating {env_template}...")

    # Read the file
    with open(env_template, "r") as f:
        content = f.read()

    # Check if the file already has TZ setting
    if f"TZ={TIMEZONE}" in content:
        print(f"  Already has timezone setting.")
        return False

    # Add the timezone setting
    if content and not content.endswith("\n"):
        content += "\n"

    content += f"\n# Timezone\nTZ={TIMEZONE}\n"

    # Write the updated content back to the file
    with open(env_template, "w") as f:
        f.write(content)

    print(f"  Updated successfully.")
    return True


def update_env(project_dir):
    """Update .env file to include the timezone setting if it exists."""
    env_file = os.path.join(project_dir, ".env")

    if not os.path.exists(env_file):
        print(f"No .env found in {project_dir}")
        return False

    print(f"Updating {env_file}...")

    # Read the file
    with open(env_file, "r") as f:
        content = f.read()

    # Check if the file already has TZ setting
    if f"TZ={TIMEZONE}" in content:
        print(f"  Already has timezone setting.")
        return False

    # Add the timezone setting
    if content and not content.endswith("\n"):
        content += "\n"

    content += f"\n# Timezone\nTZ={TIMEZONE}\n"

    # Write the updated content back to the file
    with open(env_file, "w") as f:
        f.write(content)

    print(f"  Updated successfully.")
    return True


def main():
    """Update timezone settings in all configured projects."""
    for project in PROJECTS:
        project_dir = os.path.abspath(project)
        print(f"\nProcessing project: {project_dir}")

        # Update docker-compose.yml
        docker_compose = os.path.join(project_dir, "docker-compose.yml")
        if os.path.exists(docker_compose):
            update_docker_compose(docker_compose)
        else:
            print(f"No docker-compose.yml found in {project_dir}")

        # Update .env.template
        update_env_template(project_dir)

        # Update .env if it exists
        update_env(project_dir)


if __name__ == "__main__":
    main()
