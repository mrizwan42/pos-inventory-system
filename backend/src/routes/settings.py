from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Branch, Category
from src.models.sales import SystemSetting
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    try:
        settings = SystemSetting.query.all()
        
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.setting_key] = {
                'value': setting.setting_value,
                'description': setting.description,
                'updated_at': setting.updated_at.isoformat() if setting.updated_at else None
            }
        
        return jsonify({'settings': settings_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/<setting_key>', methods=['GET'])
@jwt_required()
def get_setting(setting_key):
    try:
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        return jsonify({'setting': setting.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/', methods=['POST'])
@jwt_required()
def create_setting():
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('setting_key') or not data.get('setting_value'):
            return jsonify({'error': 'setting_key and setting_value are required'}), 400
        
        # Check if setting already exists
        existing_setting = SystemSetting.query.filter_by(setting_key=data['setting_key']).first()
        if existing_setting:
            return jsonify({'error': 'Setting already exists'}), 400
        
        # Create new setting
        new_setting = SystemSetting(
            setting_key=data['setting_key'],
            setting_value=data['setting_value'],
            description=data.get('description'),
            updated_by=get_jwt_identity()
        )
        
        db.session.add(new_setting)
        db.session.commit()
        
        return jsonify({
            'message': 'Setting created successfully',
            'setting': new_setting.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/<setting_key>', methods=['PUT'])
@jwt_required()
def update_setting(setting_key):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        data = request.get_json()
        
        # Update setting fields
        if 'setting_value' in data:
            setting.setting_value = data['setting_value']
        
        if 'description' in data:
            setting.description = data['description']
        
        setting.updated_by = get_jwt_identity()
        setting.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Setting updated successfully',
            'setting': setting.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/<setting_key>', methods=['DELETE'])
@jwt_required()
def delete_setting(setting_key):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        db.session.delete(setting)
        db.session.commit()
        
        return jsonify({'message': 'Setting deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Branches management
@settings_bp.route('/branches', methods=['GET'])
@jwt_required()
def get_branches():
    try:
        branches = Branch.query.filter_by(is_active=True).all()
        
        return jsonify({
            'branches': [branch.to_dict() for branch in branches]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/branches', methods=['POST'])
@jwt_required()
def create_branch():
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('branch_name'):
            return jsonify({'error': 'branch_name is required'}), 400
        
        # Check if branch name already exists
        existing_branch = Branch.query.filter_by(branch_name=data['branch_name']).first()
        if existing_branch:
            return jsonify({'error': 'Branch name already exists'}), 400
        
        # Create new branch
        new_branch = Branch(
            branch_name=data['branch_name'],
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_branch)
        db.session.commit()
        
        return jsonify({
            'message': 'Branch created successfully',
            'branch': new_branch.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/branches/<int:branch_id>', methods=['PUT'])
@jwt_required()
def update_branch(branch_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        branch = Branch.query.get(branch_id)
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
        
        data = request.get_json()
        
        # Check if branch name already exists (if changed)
        if data.get('branch_name') and data['branch_name'] != branch.branch_name:
            existing_branch = Branch.query.filter_by(branch_name=data['branch_name']).first()
            if existing_branch:
                return jsonify({'error': 'Branch name already exists'}), 400
        
        # Update branch fields
        updatable_fields = ['branch_name', 'address', 'phone', 'email', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(branch, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Branch updated successfully',
            'branch': branch.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Categories management
@settings_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    try:
        categories = Category.query.filter_by(is_active=True).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('category_name'):
            return jsonify({'error': 'category_name is required'}), 400
        
        # Check if category name already exists
        existing_category = Category.query.filter_by(category_name=data['category_name']).first()
        if existing_category:
            return jsonify({'error': 'Category name already exists'}), 400
        
        # Validate parent category exists (if provided)
        if data.get('parent_category_id'):
            parent_category = Category.query.get(data['parent_category_id'])
            if not parent_category:
                return jsonify({'error': 'Parent category not found'}), 404
        
        # Create new category
        new_category = Category(
            category_name=data['category_name'],
            description=data.get('description'),
            parent_category_id=data.get('parent_category_id'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': new_category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        data = request.get_json()
        
        # Check if category name already exists (if changed)
        if data.get('category_name') and data['category_name'] != category.category_name:
            existing_category = Category.query.filter_by(category_name=data['category_name']).first()
            if existing_category:
                return jsonify({'error': 'Category name already exists'}), 400
        
        # Validate parent category exists (if changed)
        if data.get('parent_category_id') and data['parent_category_id'] != category.parent_category_id:
            if data['parent_category_id'] == category_id:
                return jsonify({'error': 'Category cannot be its own parent'}), 400
            
            parent_category = Category.query.get(data['parent_category_id'])
            if not parent_category:
                return jsonify({'error': 'Parent category not found'}), 404
        
        # Update category fields
        updatable_fields = ['category_name', 'description', 'parent_category_id', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(category, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Category updated successfully',
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/backup', methods=['POST'])
@jwt_required()
def backup_data():
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        # This is a placeholder for backup functionality
        # In a real implementation, you would export database data
        
        return jsonify({
            'message': 'Backup functionality not implemented yet',
            'timestamp': datetime.utcnow().isoformat()
        }), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

