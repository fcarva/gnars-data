import type { FacetBucket } from "../types";

type FilterToolbarProps = {
  searchValue?: string;
  searchPlaceholder?: string;
  onSearchChange?: (value: string) => void;
  selectValue?: string;
  selectOptions?: { value: string; label: string }[];
  onSelectChange?: (value: string) => void;
  groups: {
    label: string;
    value: string;
    options: FacetBucket[];
    onChange: (value: string) => void;
  }[];
};

export function FilterToolbar({
  searchValue = "",
  searchPlaceholder = "search",
  onSearchChange,
  selectValue,
  selectOptions = [],
  onSelectChange,
  groups,
}: FilterToolbarProps) {
  return (
    <section className="toolbar-panel">
      <div className="toolbar-main">
        {onSearchChange ? (
          <label className="toolbar-search">
            <span>&gt;</span>
            <input
              type="search"
              value={searchValue}
              placeholder={searchPlaceholder}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </label>
        ) : null}
        {onSelectChange ? (
          <label className="toolbar-select">
            <span>Sort</span>
            <select value={selectValue} onChange={(event) => onSelectChange(event.target.value)}>
              {selectOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>
      <div className="toolbar-groups">
        {groups.map((group) => (
          <div key={group.label} className="pill-group">
            <span className="pill-group-label">{group.label}</span>
            <div className="filter-row tight">
              <button
                type="button"
                className={group.value === "all" ? "filter-pill is-active" : "filter-pill"}
                onClick={() => group.onChange("all")}
              >
                All
              </button>
              {group.options.map((option) => (
                <button
                  key={`${group.label}:${option.value}`}
                  type="button"
                  className={group.value === option.value ? "filter-pill is-active" : "filter-pill"}
                  onClick={() => group.onChange(option.value)}
                >
                  {option.label} <small>{option.count}</small>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
