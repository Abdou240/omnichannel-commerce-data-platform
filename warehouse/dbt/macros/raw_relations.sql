{% macro raw_relation_exists(table_name, schema_name='raw') %}
  {% if not execute %}
    {{ return(false) }}
  {% endif %}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=schema_name,
      identifier=table_name
  ) %}
  {{ return(relation is not none) }}
{% endmacro %}
