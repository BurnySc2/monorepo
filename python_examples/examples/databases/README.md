# Database examples 

## Tables
### Library
- id
- name: str
- address: str
- books: List[BookInventory]

### BookInventory
- id
- book: Book
- library: Library
- amount: int

### Book
- id
- name: str
- pages: int
- release_year: int
- author: Author
- publisher: Publisher

### Author
- id
- name: str
- birth_year: int

### Publisher
- id
- name: str
- founded_year: int

## Schema diagram
```mermaid
---
title: Schema diagram
---
erDiagram
    Author ||--o{ Book : writes
    Book {
        name string
        pages int
        release_year int
        author_id int
        publisher_id int
    }
    Author {
        name string
        birth_year int
    }
    Publisher ||--o{ Book : publishes
    Publisher {
        name string
        founded_year int
    }
    Library ||--o{ BookInventory : has
    BookInventory {
        book_id int
        library_id int
        amount int
    }
    Library {
        name string
        address string
        book_id int[]
    }
    BookInventory }o--|| Book : has

```

## Query example
Each database example should have these actions as examples:

1) Create tables
2) Add new items
3) Query (select), with filters
4) Update items
5) Delete items
6) Join multiple tables
7) Join two tables and apply filter to both
8) Apply migrations (modify a table with existing data)
9) Clear table (remove all items)
