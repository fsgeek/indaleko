jq -s 'group_by(.Path) | .[] | {type:"contains", parent_uri: .[0].Path, children_uri: map(.URI)}' $1 | jq -c '.'
