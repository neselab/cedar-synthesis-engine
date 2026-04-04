"""Cedar schema string manipulation helpers.

Provides targeted regex-based operations for mutating Cedar schema files.
Not a full parser — handles the common patterns found in the dataset schemas.
"""

import re
from typing import Optional


def add_attribute(schema: str, entity_name: str, attr_name: str, attr_type: str) -> str:
    """Add an attribute to an existing entity type declaration.

    Inserts before the closing '};' of the entity block.
    Handles both quoted and unquoted attribute names.
    """
    # Match entity declaration with attributes block: entity Name = { ... };
    pattern = re.compile(
        rf'(entity\s+{re.escape(entity_name)}\b[^{{]*\{{)(.*?)(\}};)',
        re.DOTALL,
    )
    match = pattern.search(schema)
    if not match:
        raise ValueError(f"Entity '{entity_name}' with attributes block not found in schema")

    body = match.group(2)
    # Determine indentation from existing attributes
    indent = "    "
    existing_lines = [l for l in body.strip().split('\n') if l.strip()]
    if existing_lines:
        first_attr = existing_lines[0]
        indent = first_attr[:len(first_attr) - len(first_attr.lstrip())]

    # Check if there's a trailing comma on the last attribute
    body_stripped = body.rstrip()
    if body_stripped and not body_stripped.endswith(','):
        # Add comma to last attribute
        body = body.rstrip() + ','
    else:
        body = body.rstrip()

    new_attr = f"\n{indent}{attr_name}: {attr_type},"
    new_body = body + new_attr + "\n"

    return schema[:match.start()] + match.group(1) + new_body + match.group(3) + schema[match.end():]


def remove_attribute(schema: str, entity_name: str, attr_name: str) -> str:
    """Remove an attribute from an entity type declaration."""
    pattern = re.compile(
        rf'(entity\s+{re.escape(entity_name)}\b[^{{]*\{{)(.*?)(\}};)',
        re.DOTALL,
    )
    match = pattern.search(schema)
    if not match:
        raise ValueError(f"Entity '{entity_name}' with attributes block not found in schema")

    body = match.group(2)
    # Remove the line containing the attribute
    attr_pattern = re.compile(rf'^\s*"?{re.escape(attr_name)}"?\s*:.*,?\s*$', re.MULTILINE)
    new_body = attr_pattern.sub('', body)
    # Clean up empty lines
    new_body = re.sub(r'\n\s*\n\s*\n', '\n', new_body)

    return schema[:match.start()] + match.group(1) + new_body + match.group(3) + schema[match.end():]


def add_entity(schema: str, entity_def: str, before_actions: bool = True) -> str:
    """Add a new entity type declaration to the schema.

    If before_actions=True, inserts before the first 'action' declaration.
    Otherwise appends at the end.
    """
    entity_def = entity_def.strip() + '\n'

    if before_actions:
        action_match = re.search(r'^(//\s*.*action.*\n)?action\s', schema, re.MULTILINE | re.IGNORECASE)
        if action_match:
            insert_pos = action_match.start()
            return schema[:insert_pos] + '\n' + entity_def + '\n' + schema[insert_pos:]

    return schema.rstrip() + '\n\n' + entity_def


def remove_entity(schema: str, entity_name: str) -> str:
    """Remove an entity type declaration from the schema."""
    # Handle entity with attributes: entity Name = { ... };
    pattern = re.compile(
        rf'^entity\s+{re.escape(entity_name)}\b[^;]*\}};',
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(schema)
    if match:
        return schema[:match.start()] + schema[match.end():].lstrip('\n')

    # Handle entity without attributes: entity Name; or entity Name in [...];
    pattern = re.compile(
        rf'^entity\s+{re.escape(entity_name)}\b[^;]*;',
        re.MULTILINE,
    )
    match = pattern.search(schema)
    if match:
        return schema[:match.start()] + schema[match.end():].lstrip('\n')

    # Handle comma-separated entity declarations: entity A, B, C;
    pattern = re.compile(
        rf'^entity\s+.*\b{re.escape(entity_name)}\b.*?;',
        re.MULTILINE,
    )
    match = pattern.search(schema)
    if match:
        line = match.group()
        # Remove entity_name from the comma list
        names = re.findall(r'\b\w+\b', line.replace('entity', '').split('in')[0].split('=')[0])
        names = [n for n in names if n != entity_name]
        if names:
            rest = line[line.index(entity_name):]
            rest = re.sub(rf',?\s*{re.escape(entity_name)}\s*,?', '', line)
            return schema[:match.start()] + rest.strip() + schema[match.end():]
        else:
            return schema[:match.start()] + schema[match.end():].lstrip('\n')

    raise ValueError(f"Entity '{entity_name}' not found in schema")


def add_action(schema: str, action_def: str) -> str:
    """Add a new action declaration to the end of the schema."""
    return schema.rstrip() + '\n\n' + action_def.strip() + '\n'


def remove_action(schema: str, action_name: str) -> str:
    """Remove an action declaration from the schema.

    Handles both single-action declarations and comma-separated ones.
    """
    # Single action with appliesTo block
    pattern = re.compile(
        rf'^action\s+{re.escape(action_name)}\s+appliesTo\s*\{{.*?\}};',
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(schema)
    if match:
        return schema[:match.start()] + schema[match.end():].lstrip('\n')

    # Action in a comma-separated group: action a, b, c appliesTo { ... };
    pattern = re.compile(
        rf'^(action\s+)(.*?)(\s+appliesTo\s*\{{.*?\}};)',
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(schema):
        names_str = match.group(2)
        names = [n.strip().strip('"') for n in names_str.split(',')]
        clean_name = action_name.strip('"')
        if clean_name in [n.strip('"') for n in names]:
            remaining = [n for n in names if n.strip().strip('"') != clean_name]
            if remaining:
                new_names = ', '.join(remaining)
                replacement = match.group(1) + new_names + match.group(3)
                return schema[:match.start()] + replacement + schema[match.end():]
            else:
                return schema[:match.start()] + schema[match.end():].lstrip('\n')

    raise ValueError(f"Action '{action_name}' not found in schema")


def add_context_field(schema: str, action_name: str, field_name: str, field_type: str) -> str:
    """Add a context field to an action's appliesTo block.

    If the action has no context block, adds one. If it does, appends the field.
    """
    # Find the action's appliesTo block
    pattern = re.compile(
        rf'(action\s+[^;]*\b{re.escape(action_name)}\b[^;]*appliesTo\s*\{{)(.*?)(\}};)',
        re.DOTALL,
    )
    match = pattern.search(schema)
    if not match:
        raise ValueError(f"Action '{action_name}' with appliesTo block not found")

    body = match.group(2)

    # Check if context block already exists
    ctx_pattern = re.compile(r'(context\s*:\s*\{)(.*?)(\})', re.DOTALL)
    ctx_match = ctx_pattern.search(body)
    if ctx_match:
        # Add field to existing context
        ctx_body = ctx_match.group(2).rstrip()
        if ctx_body and not ctx_body.rstrip().endswith(','):
            ctx_body = ctx_body.rstrip() + ','
        ctx_body += f'\n        {field_name}: {field_type},'
        new_body = body[:ctx_match.start()] + ctx_match.group(1) + ctx_body + '\n    ' + ctx_match.group(3) + body[ctx_match.end():]
    else:
        # Add new context block before closing
        new_body = body.rstrip()
        if not new_body.rstrip().endswith(','):
            new_body = new_body.rstrip() + ','
        new_body += f'\n    context: {{\n        {field_name}: {field_type},\n    }}'

    return schema[:match.start()] + match.group(1) + new_body + '\n' + match.group(3) + schema[match.end():]


def add_type_def(schema: str, type_def: str) -> str:
    """Add a named type definition at the top of the schema (before entities)."""
    # Find first entity or type declaration
    first_decl = re.search(r'^(type|entity)\s', schema, re.MULTILINE)
    if first_decl:
        # Insert before, preserving any leading comments
        insert_pos = first_decl.start()
        return schema[:insert_pos] + type_def.strip() + '\n\n' + schema[insert_pos:]
    return type_def.strip() + '\n\n' + schema


def modify_entity_parents(schema: str, entity_name: str, new_parents: list[str]) -> str:
    """Change the 'in [...]' clause of an entity declaration.

    If new_parents is empty, removes the 'in [...]' clause.
    """
    parent_str = f" in [{', '.join(new_parents)}]" if new_parents else ""

    # Entity with attributes
    pattern = re.compile(
        rf'(entity\s+{re.escape(entity_name)})\s*(?:in\s*\[[^\]]*\])?\s*(=\s*\{{)',
        re.DOTALL,
    )
    match = pattern.search(schema)
    if match:
        return schema[:match.start()] + match.group(1) + parent_str + ' ' + match.group(2) + schema[match.end():]

    # Entity without attributes (possibly in a comma-separated list)
    # Simple case: entity Name in [...];
    pattern = re.compile(
        rf'(entity\s+{re.escape(entity_name)})\s*(?:in\s*\[[^\]]*\])?\s*(;)',
    )
    match = pattern.search(schema)
    if match:
        return schema[:match.start()] + match.group(1) + parent_str + match.group(2) + schema[match.end():]

    raise ValueError(f"Entity '{entity_name}' not found in schema for parent modification")


def add_entity_to_comma_list(schema: str, existing_entity: str, new_entity: str) -> str:
    """Add a new entity name to a comma-separated entity declaration.

    e.g., 'entity Team, UserGroup in [UserGroup];' → 'entity Team, UserGroup, NewEntity in [UserGroup];'
    """
    pattern = re.compile(
        rf'(entity\s+[^;]*\b{re.escape(existing_entity)}\b)([^;]*;)',
    )
    match = pattern.search(schema)
    if not match:
        raise ValueError(f"Entity declaration containing '{existing_entity}' not found")

    prefix = match.group(1)
    suffix = match.group(2)
    return schema[:match.start()] + prefix + ', ' + new_entity + suffix + schema[match.end():]
