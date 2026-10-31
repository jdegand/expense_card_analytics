select * from {{ source('raw_data', 'employees') }}
