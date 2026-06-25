// Données de test pour le pipeline
db = db.getSiblingDB('data_pipeline');

// Insertion de données brutes de test
db.raw_data.insertMany([
    {
        source_type: "csv",
        source_path: "/data/sales_2024.csv",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "001",
                name: "John Doe",
                amount: "1250.50",
                date: "2024-01-15",
                country: "FR",
                email: "john.doe@example.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "api",
        source_path: "GET /api/users",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "002",
                name: "Jane Smith",
                amount: "2500.00",
                date: "2024-01-16",
                country: "DE",
                email: "jane.smith@example.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "json",
        source_path: "/data/products.json",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "003",
                name: "Bob Johnson",
                amount: "750.25",
                date: "2024-01-17",
                country: "US",
                email: "bob.johnson@example.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "excel",
        source_path: "/data/inventory.xlsx",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "004",
                name: "Alice Brown",
                amount: "3200.00",
                date: "2024-01-18",
                country: "UK",
                email: "alice.brown@example.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "html",
        source_path: "https://example.com/products",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "005",
                name: "Charlie Davis",
                amount: "890.75",
                date: "2024-01-19",
                country: "CA",
                email: "charlie.davis@example.com"
            }
        },
        status: "pending"
    }
]);

print("✅ Données de test insérées dans raw_data");
print(`📝 ${db.raw_data.countDocuments()} documents insérés`);