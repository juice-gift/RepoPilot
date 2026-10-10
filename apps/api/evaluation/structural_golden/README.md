# V2 Structural Golden Repository

This is inert source data; RepoPilot never executes it. The intentionally duplicate
Python declarations, unresolved names, parameter shadowing, static aliases, class
methods, and exported TypeScript definitions have manually specified expectations
in `../structural_dataset.json`. Definition line ranges are inclusive.

The dataset lists all baseline symbols, static import bindings and extracted value
references in these files. Parameter definitions and property/type annotation
semantics are outside reference target resolution. Same-name definitions are
returned independently; an ambiguous reference must never choose one silently.

Snapshot isolation, syntax failure and database integrity use separate live tests
because they require more than one repository state. JS/JSX/TSX and additional
lexical cases use analyzer/resolver unit tests. This small golden repository is
not a claim of IDE-level semantic accuracy.

Expectations are frozen before evaluation. Hashes in the structural manifest
protect both the dataset and normalized file text across LF/CRLF checkouts.
